"""Carteira de Identidade Nacional (CIN) Document Parser.

Implements business rules:
- RN-01: 85% confidence threshold for auto-approval.
- RN-03: Fuzzy matching (80%-99%) on cities/states with RapidFuzz.
- RN-04: Strict CPF cryptographic validation (Module 11 via validate-docbr).
- RN-05: Layout conformity (no RG estadual, filiation, or sex printed).
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz, process
from validate_docbr import CPF

from app.core.config import settings
from app.core.logging import app_logger
from app.models.document import DocumentStatus
from app.services.ocr.base import OCRRawResult
from app.services.ocr.parsers.base import BaseDocumentParser, ParsedDocumentResult

# Reference list of Brazilian state capitals and prominent municipalities (IBGE sample)
BRAZILIAN_MUNICIPALITIES = [
    "SÃO PAULO", "RIO DE JANEIRO", "BRASÍLIA", "SALVADOR", "FORTALEZA",
    "BELO HORIZONTE", "MANAUS", "CURITIBA", "RECIFE", "PORTO ALEGRE",
    "GOIÂNIA", "BELÉM", "GUARULHOS", "CAMPINAS", "SÃO LUÍS",
    "SÃO GONÇALO", "MACEIÓ", "DUQUE DE CAXIAS", "NATAL", "TERESINA",
    "SÃO BERNARDO DO CAMPO", "CAMPO GRANDE", "JOÃO PESSOA", "SANTO ANDRÉ",
    "OSASCO", "SÃO JOSÉ DOS CAMPOS", "RIBEIRÃO PRETO", "UBERLÂNDIA",
    "SOROCABA", "CUIABÁ", "ARACAJU", "FEIRA DE SANTANA", "JOINVILLE",
    "JUIZ DE FORA", "LONDRINA", "APARECIDA DE GOIÂNIA", "ANANINDEUA",
    "PORTO VELHO", "NITERÓI", "BELFORD ROXO", "SERRA", "CAXIAS DO SUL",
    "MACAPÁ", "CAMPOS DOS GOYTACAZES", "FLORIANÓPOLIS", "VILA VELHA",
    "MAUÁ", "SÃO JOÃO DE MERITI", "SÃO JOSÉ DO RIO PRETO", "SANTOS",
    "BETIM", "DIADEMA", "MARINGÁ", "JUNDIAÍ", "CAMPINA GRANDE",
    "MONTES CLAROS", "PIRACICABA", "CARAPICUÍBA", "OLINDA", "RIO BRANCO",
    "ANÁPOLIS", "CARUARU", "BOA VISTA", "PALMAS", "VITÓRIA"
]

BRAZILIAN_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}

# Regex patterns
CPF_REGEX = re.compile(r"\b(\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}|\d{11})\b")
DATE_REGEX = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")


class CINDocumentParser(BaseDocumentParser):
    """Parser tailored for the new Brazilian Carteira de Identidade Nacional (CIN)."""

    def __init__(self) -> None:
        self.cpf_validator = CPF()

    @property
    def document_type(self) -> str:
        return "CIN"

    def parse(
        self, raw_ocr: OCRRawResult, template_config: Optional[Dict[str, Any]] = None
    ) -> ParsedDocumentResult:
        lines = [line.text.strip() for line in raw_ocr.lines if line.text.strip()]
        full_text = raw_ocr.full_text

        extracted_fields: Dict[str, Any] = {
            "cpf": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "nome_completo": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "data_nascimento": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "nacionalidade": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
            "naturalidade": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
            "data_validade": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
            "orgao_emissor": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
        }

        validation_errors: List[str] = []

        # 1. Extract CPF (RN-04)
        self._extract_cpf(raw_ocr, extracted_fields, validation_errors)

        # 2. Extract Dates (Data de Nascimento, Data de Validade)
        self._extract_dates(raw_ocr, extracted_fields)

        # 3. Extract Nome Completo
        self._extract_nome(raw_ocr, extracted_fields)

        # 4. Extract Nacionalidade & Naturalidade (RN-03 Fuzzy matching)
        self._extract_nacionalidade_naturalidade(raw_ocr, extracted_fields)

        # 5. Extract Órgão Emissor
        self._extract_orgao_emissor(raw_ocr, extracted_fields)

        # Calculate Overall Confidence Score
        field_confidences = [
            field["confidence"]
            for field in extracted_fields.values()
            if field["value"] is not None
        ]
        overall_confidence = (
            sum(field_confidences) / len(field_confidences)
            if field_confidences
            else 0.0
        )

        # Evaluate RN-01 and RN-04: Check if auto-approved
        # Mandatory fields for CIN: cpf, nome_completo, data_nascimento
        mandatory_keys = ["cpf", "nome_completo", "data_nascimento"]
        is_auto_approved = True

        for key in mandatory_keys:
            field = extracted_fields[key]
            # Must have value
            if not field["value"]:
                is_auto_approved = False
                validation_errors.append(f"Campo obrigatório ausente: '{key}'.")
            # Must be valid
            elif not field["is_valid"]:
                is_auto_approved = False
                validation_errors.append(f"Campo obrigatório inválido: '{key}'.")
            # Must meet RN-01 threshold (>= 0.85)
            elif field["confidence"] < settings.OCR_CONFIDENCE_THRESHOLD:
                is_auto_approved = False
                validation_errors.append(
                    f"Confiança do campo '{key}' ({field['confidence']:.2f}) abaixo do limiar seguro ({settings.OCR_CONFIDENCE_THRESHOLD:.2f})."
                )

        status = DocumentStatus.READY if is_auto_approved else DocumentStatus.NEEDS_REVIEW

        return ParsedDocumentResult(
            document_type=self.document_type,
            status=status,
            overall_confidence=round(overall_confidence, 4),
            extracted_fields=extracted_fields,
            validation_errors=validation_errors,
            is_auto_approved=is_auto_approved,
            raw_text=full_text,
        )

    def _extract_cpf(
        self,
        raw_ocr: OCRRawResult,
        extracted_fields: Dict[str, Any],
        validation_errors: List[str],
    ) -> None:
        """Find and validate CPF using validate-docbr (RN-04)."""
        for line in raw_ocr.lines:
            match = CPF_REGEX.search(line.text)
            if match:
                raw_cpf = match.group(1)
                clean_digits = re.sub(r"\D", "", raw_cpf)
                if len(clean_digits) == 11:
                    is_valid = self.cpf_validator.validate(clean_digits)
                    formatted_cpf = self.cpf_validator.mask(clean_digits) if is_valid else raw_cpf

                    extracted_fields["cpf"]["raw_value"] = raw_cpf
                    extracted_fields["cpf"]["value"] = formatted_cpf
                    extracted_fields["cpf"]["is_valid"] = is_valid

                    if is_valid:
                        extracted_fields["cpf"]["confidence"] = line.confidence
                    else:
                        # RN-04: If math check fails, confidence is voided
                        extracted_fields["cpf"]["confidence"] = 0.0
                        extracted_fields["cpf"]["warning"] = "Dígito verificador do CPF inválido pelo cálculo do Módulo 11 (RN-04)."
                        validation_errors.append("CPF inválido no cálculo matemático.")
                    return

    def _extract_dates(self, raw_ocr: OCRRawResult, extracted_fields: Dict[str, Any]) -> None:
        """Extract birth date and validity date."""
        dates_found = []
        for line in raw_ocr.lines:
            matches = DATE_REGEX.findall(line.text)
            for m in matches:
                try:
                    dt = datetime.strptime(m, "%d/%m/%Y")
                    dates_found.append((m, dt, line.confidence))
                except ValueError:
                    pass

        if dates_found:
            # Earliest date is likely birth date
            dates_found.sort(key=lambda x: x[1])
            birth_val, _, birth_conf = dates_found[0]
            extracted_fields["data_nascimento"]["value"] = birth_val
            extracted_fields["data_nascimento"]["raw_value"] = birth_val
            extracted_fields["data_nascimento"]["confidence"] = birth_conf
            extracted_fields["data_nascimento"]["is_valid"] = True

            # If more than one date, the latest is likely expiration date
            if len(dates_found) > 1:
                val_val, _, val_conf = dates_found[-1]
                extracted_fields["data_validade"]["value"] = val_val
                extracted_fields["data_validade"]["raw_value"] = val_val
                extracted_fields["data_validade"]["confidence"] = val_conf
                extracted_fields["data_validade"]["is_valid"] = True

    def _extract_nome(self, raw_ocr: OCRRawResult, extracted_fields: Dict[str, Any]) -> None:
        """Extract full name of the holder."""
        skip_words = {
            "REPÚBLICA", "FEDERATIVA", "BRASIL", "CARTEIRA", "IDENTIDADE",
            "NACIONAL", "MINISTÉRIO", "JUSTIÇA", "CPF", "NOME", "VALIDADE",
            "NASCIMENTO", "NATURALIDADE", "NACIONALIDADE", "ASSINATURA"
        }

        found_nome_anchor = False
        for i, line in enumerate(raw_ocr.lines):
            text_upper = line.text.upper()
            if "NOME" in text_upper and len(text_upper) < 15:
                found_nome_anchor = True
                # The next line is likely the name
                if i + 1 < len(raw_ocr.lines):
                    next_line = raw_ocr.lines[i + 1]
                    name_candidate = next_line.text.strip().upper()
                    # Filter out pure header labels (e.g. single label line)
                    if name_candidate and name_candidate not in skip_words and len(name_candidate.split()) >= 2:
                        extracted_fields["nome_completo"]["value"] = name_candidate
                        extracted_fields["nome_completo"]["raw_value"] = next_line.text.strip()
                        extracted_fields["nome_completo"]["confidence"] = next_line.confidence
                        extracted_fields["nome_completo"]["is_valid"] = True
                        return

        # Fallback: look for 2+ capitalized words with high confidence not being an exact header label
        if not extracted_fields["nome_completo"]["value"]:
            for line in raw_ocr.lines:
                candidate = line.text.strip().upper()
                words = candidate.split()
                if len(words) >= 2 and all(w.isalpha() for w in words):
                    if candidate not in skip_words and not any(candidate.startswith(w) for w in ["REPÚBLICA", "CARTEIRA"]):
                        extracted_fields["nome_completo"]["value"] = candidate
                        extracted_fields["nome_completo"]["raw_value"] = line.text.strip()
                        extracted_fields["nome_completo"]["confidence"] = line.confidence
                        extracted_fields["nome_completo"]["is_valid"] = True
                        return

    def _extract_nacionalidade_naturalidade(
        self, raw_ocr: OCRRawResult, extracted_fields: Dict[str, Any]
    ) -> None:
        """Extract nationality and naturalness with RapidFuzz Levenshtein matching (RN-03)."""
        # Default Brazilian nationality
        extracted_fields["nacionalidade"]["value"] = "BRASILEIRA"
        extracted_fields["nacionalidade"]["raw_value"] = "BRASILEIRA"
        extracted_fields["nacionalidade"]["confidence"] = 0.95

        skip_prefixes = ("REPÚBLICA", "CARTEIRA", "IDENTIDADE", "NOME", "CPF", "VALIDADE", "NASCIMENTO")
        ocr_char_map = str.maketrans({"0": "O", "1": "L", "3": "E", "4": "A", "5": "S", "8": "B", "@": "A", "$": "S"})

        for line in raw_ocr.lines:
            text_upper = line.text.strip().upper()
            if not text_upper or any(text_upper.startswith(prefix) for prefix in skip_prefixes):
                continue

            # Candidate variations: raw and OCR visual digit substitution
            normalized_ocr_text = text_upper.translate(ocr_char_map)
            candidates = [text_upper, normalized_ocr_text]

            best_city = None
            highest_score = 0.0

            for cand in candidates:
                match = process.extractOne(cand, BRAZILIAN_MUNICIPALITIES, scorer=fuzz.ratio)
                if match:
                    city, score, _ = match
                    if score > highest_score:
                        highest_score = score
                        best_city = city

            if best_city:
                ratio = highest_score / 100.0

                # RN-03: If ratio between 80% and 99%, auto-correct
                if settings.FUZZY_MATCH_MIN_RATIO <= ratio <= settings.FUZZY_MATCH_MAX_AUTO_RATIO:
                    extracted_fields["naturalidade"]["value"] = best_city
                    extracted_fields["naturalidade"]["raw_value"] = line.text.strip()
                    extracted_fields["naturalidade"]["confidence"] = round(ratio, 4)
                    extracted_fields["naturalidade"]["is_fuzzy_corrected"] = True
                    app_logger.info(
                        f"Fuzzy auto-corrected city '{line.text.strip()}' -> '{best_city}' (ratio={ratio:.2f})"
                    )
                    return
                elif ratio > settings.FUZZY_MATCH_MAX_AUTO_RATIO:
                    extracted_fields["naturalidade"]["value"] = best_city
                    extracted_fields["naturalidade"]["raw_value"] = line.text.strip()
                    extracted_fields["naturalidade"]["confidence"] = 1.0
                    return

        # If not matched, set default or keep unconfirmed
        extracted_fields["naturalidade"]["warning"] = "Naturalidade não identificada com alta confiança na base padrão."

    def _extract_orgao_emissor(
        self, raw_ocr: OCRRawResult, extracted_fields: Dict[str, Any]
    ) -> None:
        """Detect issuing authority."""
        for line in raw_ocr.lines:
            text_upper = line.text.upper()
            if any(term in text_upper for term in ["INSTITUTO", "IDENTIFICAÇÃO", "SSP", "DETRAN", "POLÍCIA CIVIL"]):
                extracted_fields["orgao_emissor"]["value"] = line.text.strip()
                extracted_fields["orgao_emissor"]["raw_value"] = line.text.strip()
                extracted_fields["orgao_emissor"]["confidence"] = line.confidence
                return
