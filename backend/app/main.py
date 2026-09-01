"""DOC_Intelligence FastAPI Main Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.file_security import FileSecurityError
from app.core.logging import app_logger, setup_logging
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.models.document import Document
from app.models.persona import Persona
from app.models.template import Template
from app.models.user import User, UserRole
from app.services.storage.minio_service import minio_service
from app.services.storage.path_formatter import generate_standard_filename


async def align_document_filenames() -> None:
    """Align any unformatted or raw timestamp document names in dev database to standardized nomenclature."""
    try:
        async with async_session_factory() as session:
            stmt = select(Document)
            result = await session.execute(stmt)
            docs = result.scalars().all()
            updated = False
            for doc in docs:
                if doc.sanitized_file_name:
                    name_without_ext = doc.sanitized_file_name.rsplit(".", 1)[0]
                    # Check if file has a raw numeric timestamp or generic name
                    if name_without_ext.isdigit() or name_without_ext.startswith("documento_captura_") or name_without_ext == "upload":
                        persona = await session.get(Persona, doc.persona_id) if doc.persona_id else None
                        persona_name = persona.name if persona else None
                        std_name = generate_standard_filename(
                            persona_name=persona_name,
                            persona_id=doc.persona_id or "",
                            doc_type="cin",
                            doc_id=doc.id,
                            original_filename=doc.sanitized_file_name,
                            created_at=doc.created_at,
                        )
                        doc.sanitized_file_name = std_name
                        doc.raw_file_name = std_name
                        updated = True
            if updated:
                await session.commit()
                app_logger.info("Aligned existing unformatted document filenames to standardized format.")
    except Exception as exc:
        app_logger.warning(f"Note during document filenames alignment: {exc}")


async def seed_initial_data() -> None:
    """Seed initial superuser and predefined templates (CIN and RG)."""
    async with async_session_factory() as session:
        # 1. Seed Superuser
        stmt_user = select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        existing_user = (await session.execute(stmt_user)).scalar_one_or_none()
        if not existing_user:
            admin = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="Administrador do Sistema",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            app_logger.info(f"Seeded default superuser: {settings.FIRST_SUPERUSER_EMAIL}")

        # 2. Seed Default CIN Template (RN-05)
        stmt_cin = select(Template).where(Template.code == "CIN")
        if not (await session.execute(stmt_cin)).scalar_one_or_none():
            cin_template = Template(
                code="CIN",
                name="Carteira de Identidade Nacional (Nova CIN)",
                description="Modelo unificado da Carteira de Identidade Nacional com CPF único, sem filiação física e sem RG estadual.",
                document_type="CIN",
                fields_schema=[
                    {"name": "cpf", "label": "CPF", "data_type": "string", "required": True, "min_confidence": 0.85},
                    {"name": "nome_completo", "label": "Nome Completo", "data_type": "string", "required": True, "min_confidence": 0.85},
                    {"name": "data_nascimento", "label": "Data de Nascimento", "data_type": "date", "required": True, "min_confidence": 0.85},
                    {"name": "nacionalidade", "label": "Nacionalidade", "data_type": "string", "required": False, "min_confidence": 0.80},
                    {"name": "naturalidade", "label": "Naturalidade", "data_type": "string", "required": False, "min_confidence": 0.80},
                    {"name": "data_validade", "label": "Data de Validade", "data_type": "date", "required": False, "min_confidence": 0.80},
                    {"name": "orgao_emissor", "label": "Órgão Emissor", "data_type": "string", "required": False, "min_confidence": 0.80},
                ],
                validation_rules={
                    "cpf_required": True,
                    "validate_mod11": True,
                    "layout_rules": ["no_filiation", "no_sex_field", "no_state_rg"],
                },
                is_active=True,
            )
            session.add(cin_template)
            app_logger.info("Seeded default CIN Template")

        # 3. Seed Default RG Antigo Template
        stmt_rg = select(Template).where(Template.code == "RG_ANTIGO")
        if not (await session.execute(stmt_rg)).scalar_one_or_none():
            rg_template = Template(
                code="RG_ANTIGO",
                name="Registro Geral Antigo (RG Tradicional)",
                description="Modelo estadual tradicional com número de RG e Filiação obrigatória.",
                document_type="RG_ANTIGO",
                fields_schema=[
                    {"name": "rg_numero", "label": "Número do RG", "data_type": "string", "required": True, "min_confidence": 0.85},
                    {"name": "nome_completo", "label": "Nome Completo", "data_type": "string", "required": True, "min_confidence": 0.85},
                    {"name": "filiacao", "label": "Filiação", "data_type": "string", "required": True, "min_confidence": 0.85},
                    {"name": "data_nascimento", "label": "Data de Nascimento", "data_type": "date", "required": True, "min_confidence": 0.85},
                ],
                validation_rules={"rg_required": True, "filiation_required": True},
                is_active=True,
            )
            session.add(rg_template)
            app_logger.info("Seeded default RG_ANTIGO Template")

        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifecycle."""
    setup_logging()
    app_logger.info("Starting DOC_Intelligence Backend...")

    # Auto-align existing database tables by removing obsolete workspace columns
    if engine.dialect.name == "postgresql":
        try:
            from sqlalchemy import text
            statements = [
                "ALTER TABLE IF EXISTS personas DROP CONSTRAINT IF EXISTS personas_workspace_id_fkey CASCADE",
                "ALTER TABLE IF EXISTS documents DROP CONSTRAINT IF EXISTS documents_workspace_id_fkey CASCADE",
                "ALTER TABLE IF EXISTS collection_links DROP CONSTRAINT IF EXISTS collection_links_workspace_id_fkey CASCADE",
                "ALTER TABLE IF EXISTS webhook_configs DROP CONSTRAINT IF EXISTS webhook_configs_workspace_id_fkey CASCADE",
                "ALTER TABLE IF EXISTS personas DROP COLUMN IF EXISTS workspace_id CASCADE",
                "ALTER TABLE IF EXISTS documents DROP COLUMN IF EXISTS workspace_id CASCADE",
                "ALTER TABLE IF EXISTS collection_links DROP COLUMN IF EXISTS workspace_id CASCADE",
                "ALTER TABLE IF EXISTS webhook_configs DROP COLUMN IF EXISTS workspace_id CASCADE",
                "DROP TABLE IF EXISTS workspaces CASCADE",
            ]
            async with engine.begin() as conn:
                app_logger.info("Verifying and aligning PostgreSQL schema for MVP...")
                for stmt in statements:
                    try:
                        await conn.execute(text(stmt))
                    except Exception:
                        pass
                app_logger.info("Schema aligned successfully (obsolete workspace columns removed).")
        except Exception as e:
            app_logger.warning(f"Note during schema alignment: {e}")

    # Create tables if not exist (dev setup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure MinIO bucket exists
    minio_service.ensure_bucket_exists()

    # Seed Initial Data
    await seed_initial_data()

    # Align existing documents filenames if any unformatted exist
    await align_document_filenames()

    yield

    app_logger.info("Shutting down DOC_Intelligence Backend...")
    await engine.dispose()


def create_app() -> FastAPI:
    """FastAPI Application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers em Português Semântico e Amigável ao Usuário Final
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        detalhes_erros = []
        for err in exc.errors():
            loc = err.get("loc", ())
            campo = str(loc[-1]) if loc else "campo"
            tipo = err.get("type", "")
            raw_msg = err.get("msg", "")

            if "missing" in tipo:
                msg_formatada = f"O campo '{campo}' é obrigatório e não foi informado."
            elif "string_too_short" in tipo:
                msg_formatada = f"O campo '{campo}' não atinge o tamanho mínimo exigido."
            elif "value_error" in tipo:
                msg_formatada = raw_msg.replace("Value error, ", "").strip()
            else:
                msg_formatada = raw_msg

            detalhes_erros.append({
                "campo": campo,
                "mensagem": msg_formatada,
                "tipo_validacao": tipo,
            })

        primeira_msg = detalhes_erros[0]["mensagem"] if detalhes_erros else "Dados da requisição inválidos."

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": primeira_msg,
                "sucesso": False,
                "codigo_status": 422,
                "tipo_erro": "DADOS_INVALIDOS",
                "mensagem": "Um ou mais campos enviados contêm inconsistências ou estão em formato inválido.",
                "detalhes": detalhes_erros,
            },
        )

    @app.exception_handler(FileSecurityError)
    async def file_security_exception_handler(request: Request, exc: FileSecurityError):
        app_logger.warning(f"FileSecurityError: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "sucesso": False,
                "codigo_status": 422,
                "tipo_erro": "ARQUIVO_INSEGURO_OU_INVALIDO",
                "mensagem": str(exc),
                "detalhes": "A inspeção de segurança em memória rejeitou o arquivo antes do armazenamento.",
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        tipo_map = {
            400: "REQUISICAO_INVALIDA",
            401: "NAO_AUTORIZADO",
            403: "ACESSO_PROIBIDO",
            404: "NAO_ENCONTRADO",
            409: "CONFLITO_CONCORRENCIA",
            422: "ENTIDADE_IMPROCESSAVEL",
            500: "ERRO_INTERNO_SERVIDOR",
        }
        tipo_erro = tipo_map.get(exc.status_code, "ERRO_HTTP")
        mensagem = exc.detail if isinstance(exc.detail, str) else "Ocorreu um erro no processamento da requisição."

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": mensagem,
                "sucesso": False,
                "codigo_status": exc.status_code,
                "tipo_erro": tipo_erro,
                "mensagem": mensagem,
                "detalhes": exc.detail if not isinstance(exc.detail, str) else None,
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        app_logger.exception(f"Unhandled Exception: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Ocorreu um erro interno inesperado no servidor. Nossa equipe foi notificada.",
                "sucesso": False,
                "codigo_status": 500,
                "tipo_erro": "ERRO_INTERNO_SERVIDOR",
                "mensagem": "Ocorreu um erro interno inesperado no servidor. Nossa equipe foi notificada.",
                "detalhes": None,
            },
        )

    # Include API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health", tags=["Health"])
    async def healthcheck():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "0.1.0",
        }

    return app


app = create_app()
