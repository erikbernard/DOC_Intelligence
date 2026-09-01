"""Mock OCR Strategy Adapter implementing BaseOCREngine.

Provides simulated fast OCR extractions:
- 8 out of 10 documents are complete and auto-approved (READY)
- 2 out of 10 documents contain realistic simulated flaws (NEEDS_REVIEW)
  requiring human operator side-by-side inspection and manual review.
"""

import time
from typing import Any, Dict, List, Optional
import numpy as np
from validate_docbr import CPF

from app.core.logging import app_logger
from app.services.ocr.base import (
    BaseOCREngine,
    OCRBoundingBox,
    OCRLineResult,
    OCRRawResult,
)


MOCK_PROFILES = [
    # 0. Sucesso (Auto-Aprovado)
    {
        "nome": "ANA CLARA SILVA SANTOS",
        "data_nasc": "14/03/1995",
        "naturalidade": "SÃO PAULO - SP",
        "validade": "14/03/2035",
        "orgao": "SSP/SP",
        "should_fail": False,
        "failure_mode": None,
    },
    # 1. Sucesso (Auto-Aprovado)
    {
        "nome": "BRUNO HENRIQUE OLIVEIRA",
        "data_nasc": "22/07/1988",
        "naturalidade": "RIO DE JANEIRO - RJ",
        "validade": "22/07/2034",
        "orgao": "DETRAN/RJ",
        "should_fail": False,
        "failure_mode": None,
    },
    # 2. Sucesso (Auto-Aprovado)
    {
        "nome": "CAMILA FERREIRA LIMA",
        "data_nasc": "05/11/2001",
        "naturalidade": "FORTALEZA - CE",
        "validade": "05/11/2033",
        "orgao": "SSPDS/CE",
        "should_fail": False,
        "failure_mode": None,
    },
    # 3. Sucesso (Auto-Aprovado)
    {
        "nome": "DIEGO ALVES PEREIRA",
        "data_nasc": "30/09/1993",
        "naturalidade": "BELO HORIZONTE - MG",
        "validade": "30/09/2034",
        "orgao": "PCMG",
        "should_fail": False,
        "failure_mode": None,
    },
    # 4. Falha 1 (Revisão Manual Necessária) - Dígito verificador de CPF inválido (RN-04)
    {
        "nome": "EDUARDO MARTINS ROCHA",
        "data_nasc": "18/02/1986",
        "naturalidade": "CURITIBA - PR",
        "validade": "18/02/2034",
        "orgao": "SESP/PR",
        "should_fail": True,
        "failure_mode": "corrupted_cpf",
    },
    # 5. Sucesso (Auto-Aprovado)
    {
        "nome": "FERNANDA GOMES RIBEIRO",
        "data_nasc": "12/12/1997",
        "naturalidade": "SALVADOR - BA",
        "validade": "12/12/2035",
        "orgao": "SPTC/BA",
        "should_fail": False,
        "failure_mode": None,
    },
    # 6. Sucesso (Auto-Aprovado)
    {
        "nome": "GABRIEL SOUZA BARBOSA",
        "data_nasc": "08/04/1990",
        "naturalidade": "RECIFE - PE",
        "validade": "08/04/2034",
        "orgao": "SDS/PE",
        "should_fail": False,
        "failure_mode": None,
    },
    # 7. Sucesso (Auto-Aprovado)
    {
        "nome": "HELENA CARDOSO DIAS",
        "data_nasc": "27/08/1999",
        "naturalidade": "PORTO ALEGRE - RS",
        "validade": "27/08/2035",
        "orgao": "IGP/RS",
        "should_fail": False,
        "failure_mode": None,
    },
    # 8. Sucesso (Auto-Aprovado)
    {
        "nome": "IGOR NASCIMENTO CASTRO",
        "data_nasc": "19/01/1992",
        "naturalidade": "GOIÂNIA - GO",
        "validade": "19/01/2034",
        "orgao": "SPTC/GO",
        "should_fail": False,
        "failure_mode": None,
    },
    # 9. Falha 2 (Revisão Manual Necessária) - Campo obrigatório ausente e baixa confiança
    {
        "nome": "JULIANA TAVARES MELO",
        "data_nasc": "03/06/1994",
        "naturalidade": "MANAUS - AM",
        "validade": "03/06/2034",
        "orgao": "SSP/AM",
        "should_fail": True,
        "failure_mode": "low_confidence_and_missing",
    },
]


class MockOCREngineAdapter(BaseOCREngine):
    """Simulated OCR engine for rapid development and staging demonstrations."""

    def __init__(self) -> None:
        self._counter: int = 0
        self._cpf_generator = CPF()

    @property
    def engine_name(self) -> str:
        return "MockOCR_v1"

    def reset_counter(self) -> None:
        """Reset sequence counter (useful for reproducible unit tests)."""
        self._counter = 0

    def extract(
        self, image_np: np.ndarray, metadata: Optional[Dict[str, Any]] = None
    ) -> OCRRawResult:
        """Produce synthetic OCR lines following the 80% success / 20% manual review rule."""
        start_time = time.time()
        idx = self._counter % len(MOCK_PROFILES)
        self._counter += 1

        profile = MOCK_PROFILES[idx]
        lines_data: List[tuple] = []

        if not profile["should_fail"]:
            # Standard auto-approved CIN document (RN-01, RN-04)
            valid_cpf = self._cpf_generator.generate(mask=True)
            lines_data = [
                ("REPÚBLICA FEDERATIVA DO BRASIL", 0.99),
                ("CARTEIRA DE IDENTIDADE NACIONAL", 0.99),
                ("NOME / NAME", 0.98),
                (profile["nome"], 0.98),
                ("CPF", 0.99),
                (valid_cpf, 0.99),
                ("DATA DE NASCIMENTO / DATE OF BIRTH", 0.97),
                (profile["data_nasc"], 0.97),
                ("SEXO / SEX", 0.95),
                ("F" if "A" in profile["nome"].split()[0][-1] else "M", 0.95),
                ("NACIONALIDADE / NATIONALITY", 0.98),
                ("BRASILEIRA", 0.98),
                ("NATURALIDADE / PLACE OF BIRTH", 0.96),
                (profile["naturalidade"], 0.96),
                ("DATA DE VALIDADE / EXPIRATION DATE", 0.96),
                (profile["validade"], 0.97),
                ("ÓRGÃO EXPEDIDOR / ISSUING BODY", 0.95),
                (profile["orgao"], 0.95),
            ]
        elif profile["failure_mode"] == "corrupted_cpf":
            # Failure 1: Corrupted CPF check digits (e.g. glare on numbers) -> NEEDS_REVIEW
            invalid_cpf = "123.456.789-00"
            lines_data = [
                ("REPÚBLICA FEDERATIVA DO BRASIL", 0.99),
                ("CARTEIRA DE IDENTIDADE NACIONAL", 0.99),
                ("NOME / NAME", 0.98),
                (profile["nome"], 0.98),
                ("CPF", 0.98),
                (invalid_cpf, 0.65),
                ("DATA DE NASCIMENTO / DATE OF BIRTH", 0.97),
                (profile["data_nasc"], 0.97),
                ("NATURALIDADE / PLACE OF BIRTH", 0.95),
                (profile["naturalidade"], 0.95),
                ("DATA DE VALIDADE / EXPIRATION DATE", 0.95),
                (profile["validade"], 0.96),
            ]
        else:
            # Failure 2: Occluded / cropped image with missing date and low confidence -> NEEDS_REVIEW
            valid_cpf = self._cpf_generator.generate(mask=True)
            lines_data = [
                ("IDENTIDADE", 0.45),
                ("NOME / NAME", 0.95),
                ("??? NOME ILEGIVEL / BORRADO ???", 0.40),
                ("CPF", 0.98),
                (valid_cpf, 0.98),
                ("ÓRGÃO EXPEDIDOR", 0.80),
                (profile["orgao"], 0.85),
            ]

        lines: List[OCRLineResult] = []
        full_text_pieces: List[str] = []

        for i, (text_content, conf) in enumerate(lines_data):
            bbox = OCRBoundingBox(
                x_min=40,
                y_min=i * 35 + 20,
                x_max=450,
                y_max=i * 35 + 50,
            )
            line = OCRLineResult(
                text=text_content,
                confidence=float(conf),
                bbox=bbox,
            )
            lines.append(line)
            full_text_pieces.append(text_content)

        elapsed_ms = (time.time() - start_time) * 1000.0 + 15.0  # simulate ~15ms processing
        full_text = "\n".join(full_text_pieces)

        app_logger.info(
            f"MockOCR extracted profile #{idx} ('{profile['nome']}') - Failure simulated: {profile['should_fail']}"
        )

        return OCRRawResult(
            engine_name=self.engine_name,
            lines=lines,
            full_text=full_text,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={
                "profile_index": idx,
                "should_fail": profile["should_fail"],
                "failure_mode": profile.get("failure_mode"),
            },
        )
