# Plano de Implementação: Backend de Document Intelligence (OCR CIN, MinIO, Filas & Auditoria)

Este documento detalha o design arquitetural, regras de negócio estritas (RN-01 a RN-15), estrutura de banco de dados, padrões de projeto e plano de execução para o desenvolvimento do backend do **DOC_Intelligence** na pasta `backend/`.

---

## 1. Visão Geral da Arquitetura & Fluxo de Eventos

O sistema é construído sobre **FastAPI (Python 3.12/asyncio)**, **PostgreSQL 16** via **SQLAlchemy 2.0 Async**, **Redis 7** (Broker Celery, TTL Locks, SSE Pub/Sub), **Celery Workers** para tarefas assíncronas e **MinIO S3** para armazenamento particionado de documentos.

```mermaid
flowchart TD
    subgraph ClientLayer["Camada de Clientes"]
        AdminUI["Frontend Operador / Conferente"]
        PublicClient["Usuário Comum (Link de Coleta)"]
        ExternalSys["Sistemas Externos (Webhooks)"]
    end

    subgraph APILayer["FastAPI Gateway (backend/app/api)"]
        Auth["Auth JWT & Tokens Efêmeros"]
        SecInspect["Validador Multicamada em Memória\n(Magic Bytes, PDF JS/Macros, Pixel Bombs)"]
        DocRoutes["Rotas de Documentos / Personas / Templates"]
        SSERoute["Endpoint SSE (/api/v1/documents/stream)"]
    end

    subgraph StorageLayer["Armazenamento & Estado"]
        Postgres[(PostgreSQL 16 - Metadados & Auditoria)]
        MinIO[(MinIO S3 - Bucket seguro de Documentos)]
        Redis[(Redis 7 - Broker Celery, TTL Locks 10min, SSE PubSub)]
    end

    subgraph WorkerLayer["Processamento Assíncrono (Celery Workers)"]
        DocWorker["Worker de OCR & Pipeline"]
        WebhookWorker["Worker de Dispatch de Webhooks"]
    end

    subgraph OCRCore["OCR Engine (Strategy + Adapter)"]
        OCRContext["OCR Context / Orchestrator"]
        subgraph Strategies["Estratégias Concretas (Adapters)"]
            EasyOCRAdapter["OpenCV Deskew + EasyOCR Adapter"]
            RapidOCRAdapter["RapidOCR / ONNX Adapter (Fallback)"]
        end
        PostProc["Pós-Processamento CIN:\nvalidate-docbr (CPF) + RapidFuzz (IBGE)"]
    end

    PublicClient -->|Upload via Link Seguro (48h)| SecInspect
    AdminUI -->|Upload / Gestão / Revisão| SecInspect
    SecInspect -->|Arquivo Válido| DocRoutes
    DocRoutes -->|Persistência Inicial| Postgres
    DocRoutes -->|Salva Arquivo com Máscara| MinIO
    DocRoutes -->|Enfileira Task| Redis
    Redis -->|Consome Task| DocWorker
    DocWorker -->|Rasterização 300 DPI pypdfium2| MinIO
    DocWorker -->|Executa| OCRContext
    OCRContext --> EasyOCRAdapter
    EasyOCRAdapter --> PostProc
    DocWorker -->|RN-01: Confiança >= 85% e CPF Válido?| Postgres
    DocWorker -->|Publica Evento SSE| Redis
    Redis -->|Streaming SSE| SSERoute
    SSERoute -->|Real-time update| AdminUI
    DocWorker -->|Dispara Webhook Task| Redis
    Redis --> WebhookWorker
    WebhookWorker -->|POST HMAC c/ Retentativas| ExternalSys
```

---

## 2. Regras de Negócio Implementadas (RN-01 a RN-15)

### 2.1. Processamento, Extração e Qualidade (OCR)
- **RN-01 (Retenção Obrigatória por Baixa Confiança)**:
  - Limiar de aprovação automática: **85%** (0.85) em cada campo obrigatório.
  - Se qualquer campo obrigatório tiver confiança `< 0.85` ou for nulo/vazio, status vai obrigatoriamente para `NEEDS_REVIEW` (Pendente na Fila de Conferência).
- **RN-02 (Dedução de Template e Fallback)**:
  - Se o upload não informar o template, o motor classifica a imagem. Se a confiança da classificação for `< 90%` (0.90), a extração não é executada e o documento vai para a Fila de Conferência com status `TEMPLATE_NOT_IDENTIFIED`.
- **RN-03 (Normalização Ortográfica - Fuzzy Matching)**:
  - Para campos como Naturalidade/Cidades:
    - Similaridade Levenshtein com tabela de municípios do IBGE entre **80% e 99%** (`0.80 <= ratio < 1.0`): **correção automática** (ex: "S4O PAU10" $\to$ "SÃO PAULO").
    - Similaridade `< 80%`: mantém texto original e sinaliza alerta de atenção (`fuzzy_warning = true`).
- **RN-04 (Validação Criptográfica de Identificadores)**:
  - Validação estrita do CPF via cálculo de módulo 11 com `validate-docbr`.
  - **Regra de Ouro**: Se o CPF falhar na validação matemática, a confiança visual do OCR é ignorada e o documento é compulsoriamente enviado para revisão humana (`NEEDS_REVIEW`).
- **RN-05 (Conformidade de Leiaute - RG vs. CIN)**:
  - **Template CIN (Nova Identidade)**: Não exige nem busca "RG Estadual", "Filiação" e "Sexo" (ausentes na via impressa física). CPF é o identificador único.
  - **Template RG Antigo**: Exige "RG Estadual" e "Filiação" (Pai e Mãe).
- **RN-06 (Padronização de Rasterização - PDFs)**:
  - Conversão de páginas PDF para imagem usando `pypdfium2` cravada estritamente em **300 DPI** para preservar microletras e caracteres numismáticos.

### 2.2. Operação e Intervenção Humana (Fila de Conferência)
- **RN-07 (Exclusividade de Revisão - Locking Pessimista)**:
  - Acesso de edição a documento em análise é exclusivo a 1 único Usuário Sistema.
  - Chave Redis: `lock:doc:{doc_id}` com payload `{ "user_id": "...", "session_id": "..." }`.
  - Tentativas simultâneas retornam erro **HTTP 409 (Conflict)** detalhando o usuário revisor atual.
- **RN-08 (Expiração de Bloqueio - TTL do Lock)**:
  - TTL fixado no Redis em **10 minutos** (600 segundos).
  - Se expirar sem submissão (`PUT /api/v1/documents/{doc_id}/review`), o lock cai automaticamente e o documento retorna ao status `NEEDS_REVIEW`.
- **RN-09 (Rejeição Definitiva de Qualidade)**:
  - Endpoint `POST /api/v1/documents/{doc_id}/reject` para imagens ilegíveis/borradas.
  - Marca status como `REJECTED`, registra justificativa do operador e engatilha evento Webhook/SSE solicitando novo envio do documento pelo cliente.
- **RN-10 (Imutabilidade e Auditoria)**:
  - Documentos aprovados (`READY`) tornam-se imutáveis para operadores.
  - Persiste obrigatoriamente `approved_by_user_id` e `approved_at`.
  - Edição posterior é restrita a usuários com perfil `ADMIN`.

### 2.3. Acesso, Segurança e LGPD
- **RN-11 (Isolamento de Perspectiva do Cliente)**:
  - Usuário Comum acessa via token efêmero assinado no link seguro.
  - Permissão restrita exclusivamente a `POST /api/v1/public/upload` para a respectiva Persona. Tentativas de acessar outras rotas retornam **HTTP 403 (Forbidden)**.
- **RN-12 (Expiração de Link de Coleta)**:
  - Links de coleta possuem validade máxima de **48 horas**. Links expirados retornam resposta amigável instruindo contato com o atendimento.
- **RN-13 (Remoção Segura e em Cascata - Right to be Forgotten)**:
  - Exclusão de Persona executa **Hard Delete** total: remoção em cascata no PostgreSQL e deleção irreversível de todos os objetos correspondentes no MinIO S3 (sem soft-delete).
- **RN-14 (Mascaramento de Dados Sensíveis nos Logs)**:
  - Filtro customizado de logging estruturado (Loguru/Python Logging): **bloqueio total de PII** (CPF, nomes, filiação, RG). Logs registram unicamente identificadores de sistema (`doc_id`, `persona_id`, `task_id`, `status`).
- **RN-15 (Completude da Persona)**:
  - Verificação automática após aprovação de documento: a Persona atinge o status `ONBOARDING_COMPLETED` quando todos os documentos obrigatórios exigidos em seu perfil estiverem no status `READY`.

---

## 3. Segurança Multicamada em Memória

Antes de qualquer gravação no MinIO ou enfileiramento no Celery:
1. **Magic Bytes & MIME Sniffing**: Verificação estrita com `puremagic` / assinatura de bytes (`image/jpeg`, `image/png`, `application/pdf`).
2. **Inspeção Estrutural de PDFs**: Varredura contra scripts `/JavaScript`, `/JS`, `/Launch`, `/EmbeddedFiles` ou ações executáveis embutidas (bloqueio com HTTP 422).
3. **Prevenção de Decompression / Pixel Bombs**: Limite de descompressão Pillow (`Image.MAX_IMAGE_PIXELS = 89_000_000`) e limite de 25MB por arquivo.
4. **Sanitização de Nome**: Remoção de caracteres inseguros e prevenção de path traversal.

---

## 4. Nomenclatura Customizável e Acesso a Arquivos

- **Máscara Configurável**:
  `{workspace_id}/personas/{persona_id}/{doc_type}/{YYYY}/{MM}/{doc_id}_{sanitized_name}.{ext}`
- **Visualização de Arquivos para Usuário Autenticado**:
  - Endpoint seguro `/api/v1/documents/{doc_id}/preview` que gera URL pré-assinada do MinIO ou efetua streaming autenticado para exibição lado a lado na tela de detalhes e na Fila de Conferência.

---

## 5. Estrutura Completa de Diretórios (`backend/`)

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                    # Injeção de dependências (get_db, get_current_user, get_redis, check_admin)
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py            # Login JWT, Refresh, Me
│   │       │   ├── workspaces.py      # CRUD de Workspaces
│   │       │   ├── personas.py        # CRUD de Personas (c/ Hard Delete Cascade MinIO + DB - RN-13)
│   │       │   ├── templates.py       # CRUD de Templates (CIN e RG Antigo - RN-05)
│   │       │   ├── collection_links.py# Geração de links seguros (48h - RN-12)
│   │       │   ├── public_upload.py   # Upload do Usuário Comum com Token Efêmero (RN-11)
│   │       │   ├── documents.py       # Upload interno, listagem, filtros, preview, lock (RN-07/08), review PUT (RN-10), reject (RN-09)
│   │       │   ├── sse.py             # Streaming de eventos SSE via Redis PubSub
│   │       │   └── webhooks.py        # Configuração de webhooks e logs de entrega
│   │       └── router.py              # Agregador de rotas v1
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings (.env, MinIO, Postgres, Redis, OCR thresholds)
│   │   ├── logging.py                 # Logger com Mascaramento de PII (RN-14)
│   │   ├── security.py                # Hashing bcrypt, JWT do sistema e tokens efêmeros públicos
│   │   └── file_security.py           # Validador multicamada em memória (Magic Bytes, PDF JS, Pixel Bombs)
│   ├── db/
│   │   ├── base.py                    # Base declarativa SQLAlchemy
│   │   └── session.py                 # AsyncSession SQLAlchemy 2.0 engine e sessionmaker
│   ├── models/
│   │   ├── user.py                    # User (ADMIN, OPERATOR)
│   │   ├── workspace.py               # Workspace (máscara de arquivos customizável)
│   │   ├── persona.py                 # Persona (status: PENDING, ONBOARDING_COMPLETED - RN-15)
│   │   ├── template.py                # Template (regras de validação, campos obrigatórios)
│   │   ├── document.py                # Document (status, dados extraídos, confianças, storage path, approved_by/at)
│   │   ├── collection_link.py         # CollectionLink (token hash, expires_at 48h, max_uses)
│   │   ├── webhook.py                 # WebhookConfig e WebhookDeliveryLog
│   │   └── audit.py                   # AuditLog
│   ├── schemas/
│   │   ├── user.py                    # Schemas Pydantic v2 para Auth & Users
│   │   ├── workspace.py               # Schemas de Workspace
│   │   ├── persona.py                 # Schemas de Persona
│   │   ├── template.py                # Schemas de Template (CIN e RG Antigo)
│   │   ├── document.py                # Schemas de Documento, extração, revisão e locking
│   │   ├── collection_link.py         # Schemas de Links de Coleta
│   │   └── webhook.py                 # Schemas de Webhooks
│   ├── services/
│   │   ├── storage/
│   │   │   ├── minio_service.py       # Cliente MinIO S3 (upload, presigned URLs, cascade hard delete)
│   │   │   └── path_formatter.py      # Formatador de nomenclatura customizável de arquivos
│   │   ├── ocr/
│   │   │   ├── base.py                # BaseOCREngine (Strategy Interface)
│   │   │   ├── context.py             # OCRContext (Strategy selector & Orchestrator)
│   │   │   ├── preprocessor.py        # OpenCV deskew, contrast, ROI segmenter
│   │   │   ├── adapters/
│   │   │   │   └── easyocr_adapter.py # EasyOCR Adapter concreto
│   │   │   └── parsers/
│   │   │       ├── base.py
│   │   │       ├── cin_parser.py      # Parser específico CIN + validate-docbr + RapidFuzz (RN-01/03/04/05)
│   │   │       └── rg_parser.py       # Parser RG Antigo (RN-05)
│   │   ├── lock_service.py            # Pessimistic Locking com Redis TTL 10min (RN-07/08)
│   │   ├── sse_service.py             # Publicador e listener de eventos SSE via Redis
│   │   ├── persona_service.py         # Gestão de completude da Persona (RN-15) e Cascade Hard Delete (RN-13)
│   │   └── audit_service.py           # Registrador de auditoria estruturada
│   ├── workers/
│   │   ├── celery_app.py              # Instância e configuração do Celery
│   │   └── tasks/
│   │       ├── ocr_tasks.py           # Tarefa Celery de rasterização 300 DPI, OCR, validação e notificação
│   │       └── webhook_tasks.py       # Tarefa Celery de despacho de webhook com HMAC e retentativas
│   └── main.py                        # FastAPI Application entrypoint & lifespan events
├── tests/
│   ├── conftest.py                    # Fixtures pytest, test DB async, mock MinIO/Redis
│   ├── test_file_security.py          # Testes de Magic bytes, PDF malicioso e pixel bombs
│   ├── test_path_formatter.py         # Testes de máscaras customizáveis
│   ├── test_ocr_cin_rules.py          # Testes das regras RN-01 (85%), RN-03 (Fuzzy 80-99%), RN-04 (CPF Módulo 11)
│   ├── test_locking_ttl.py            # Testes de concorrência e TTL de 10 min (RN-07/08)
│   ├── test_persona_lifecycle.py      # Testes de Hard Delete Cascade (RN-13) e Completude (RN-15)
│   └── test_api_endpoints.py          # Testes de endpoints de API (Auth, Upload, Review, SSE, Rejection)
├── docker-compose.yml                 # PostgreSQL, Redis, MinIO (com bucket setup), API e Celery Worker
├── Dockerfile                         # Multi-stage Dockerfile para API e Celery Worker
├── pyproject.toml                     # Dependências do projeto (FastAPI, Celery, OpenCV, EasyOCR, etc.)
├── .env.example                       # Variáveis de ambiente de exemplo
└── README.md                          # Documentação de execução e guia de uso
```

---

## 6. Plano de Verificação

### Testes Automatizados
- **Segurança de Arquivos**: Injeção de scripts em PDF, falsificação de extensão e estouro de pixels.
- **Regras de Negócio OCR**:
  - Score de confiança `< 0.85` enviando para `NEEDS_REVIEW` (RN-01).
  - CPF visualmente "lido" mas matematicamente inválido sendo rejeitado para conferência humana (RN-04).
  - Município com erro tipográfico corrigido automaticamente via RapidFuzz (RN-03).
  - Template CIN ignorando campos de filiação/sexo/RG estadual (RN-05).
- **Locking e Concorrência**: Tentativa de aquisição de lock simultâneo (HTTP 409) e timeout de 10 minutos (RN-07 e RN-08).
- **Ciclo de Vida da Persona**: Hard delete no MinIO e Postgres (RN-13) e transição de completude da Persona (RN-15).
- **Imutabilidade e Rejeição**: Rejeição de imagem borrada com notificação (RN-09) e bloqueio de alteração sem perfil de administrador após aprovação (RN-10).
