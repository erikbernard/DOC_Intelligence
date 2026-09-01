# DOC_Intelligence Backend

Backend assíncrono para Onboarding, Validação Multicamada em Memória, Armazenamento Customizável no MinIO (S3) e Extração OCR de Documentos de Identidade Brasileiros (com foco na Carteira de Identidade Nacional - CIN).

---

## 🛠️ Pilha Tecnológica

- **Linguagem & Framework**: Python 3.11+, FastAPI (ASGI assíncrono)
- **Banco de Dados**: PostgreSQL 16 com SQLAlchemy 2.0 Async (`asyncpg`) e Alembic
- **Mensageria & Filas**: Redis 7 como Broker + Celery Workers com filas dedicadas (`ocr`, `webhooks`, `default`)
- **Armazenamento S3**: MinIO com suporte a buckets isolados, URLs pré-assinadas e *Hard Delete Cascade*
- **Motor OCR (Padrão Strategy + Adapter)**:
  - Higienização e alinhamento de perspectiva com OpenCV (`cv2.warpPerspective`, CLAHE)
  - Extração com EasyOCR (`pt`, `en`)
  - Parser especializado para a nova Carteira de Identidade Nacional (CIN)
  - Validação estrita do CPF via cálculo de módulo 11 com `validate-docbr`
  - Normalização ortográfica automática de municípios com `RapidFuzz`
- **Controle de Concorrência**: Locking pessimista com TTL de 10 minutos no Redis
- **Notificações**:
  - Frontend: Server-Sent Events (SSE) via Redis Pub/Sub
  - Sistemas Externos: Webhooks HTTP com assinatura criptográfica HMAC-SHA256 e retentativas exponenciais

---

## 📋 Regras de Negócio Implementadas (RN-01 a RN-15)

1. **RN-01**: Limiar de 85% de confiança por campo obrigatório; caso contrário, vai para a Fila de Conferência (`NEEDS_REVIEW`).
2. **RN-02**: Dedução de template com limiar de 90%; se inferior, direciona para classificação humana (`TEMPLATE_NOT_IDENTIFIED`).
3. **RN-03**: Correção ortográfica de cidades via RapidFuzz entre 80% e 99% de similaridade Levenshtein.
4. **RN-04**: Validação criptográfica do CPF (módulo 11); se falhar, o score visual do OCR é anulado e o documento é enviado para revisão.
5. **RN-05**: Conformidade de layout da CIN (não exige e não busca RG estadual, filiação ou sexo impressos).
6. **RN-06**: Rasterização de PDFs em memória estritamente a 300 DPI (`pypdfium2`).
7. **RN-07**: Exclusividade de revisão na Fila de Conferência (HTTP 409 Conflict para edições simultâneas).
8. **RN-08**: Time-To-Live (TTL) de 10 minutos para locks no Redis.
9. **RN-09**: Rejeição definitiva de qualidade de imagem (`REJECTED`) com emissão de evento para reenvio.
10. **RN-10**: Imutabilidade de documentos aprovados (`READY`), persistindo `approved_by` e `approved_at`.
11. **RN-11**: Isolamento de acesso do Usuário Comum via tokens efêmeros restritos a upload.
12. **RN-12**: Links de coleta com expiração de 48 horas.
13. **RN-13**: Exclusão em cascata (*Hard Delete*) no PostgreSQL e MinIO (LGPD Right to be Forgotten).
14. **RN-14**: Mascaramento automático de PII (CPF, nomes) nos logs do sistema.
15. **RN-15**: Atualização automática de status da Persona para `ONBOARDING_COMPLETED` quando todos os documentos obrigatórios estiverem `READY`.

---

## 🚀 Como Executar com Docker Compose

O arquivo `docker-compose.yml` inclui todos os serviços (PostgreSQL, Redis, MinIO, auto-criação de bucket, API FastAPI e Celery Worker).

```bash
cd backend
docker-compose up --build -d
```

### URLs de Acesso

- **Documentação da API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Console do MinIO**: [http://localhost:9001](http://localhost:9001) (Usuário: `minioadmin` / Senha: `minioadmin`)
- **API Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)

### Credenciais Padrão do Superusuário

- **E-mail**: `admin@docintelligence.com`
- **Senha**: `adminpassword123`

---

## 🧪 Execução dos Testes Automatizados

Para rodar os testes unitários e de integração:

```bash
cd backend
pytest -v
```

---

## 📮 Postman Collection & Environment

Arquivos prontos para importação direta no Postman localizados na pasta `backend/postman/`:

1. **Collection**: [`DOC_Intelligence.postman_collection.json`](file:///d:/DOC_Intelligence/backend/postman/DOC_Intelligence.postman_collection.json)
2. **Environment**: [`DOC_Intelligence.postman_environment.json`](file:///d:/DOC_Intelligence/backend/postman/DOC_Intelligence.postman_environment.json)

### Recursos do Postman:
- **Captura Automática de Variáveis**: Ao rodar a requisição de Login, o token JWT é salvo automaticamente em `{{bearer_token}}`.
- **Cadeia de IDs Automática**: Ao criar Persona, Link de Coleta ou Documento, as variáveis `{{persona_id}}`, `{{collection_token}}` e `{{document_id}}` são preenchidas para uso imediato nas próximas requisições.
- **Pastas Organizadas**:
  - `00. Health & Status`
  - `01. Autenticação & Usuários`
  - `02. Personas (Candidatos Onboarding)`
  - `03. Templates de Documentos`
  - `04. Links de Coleta Segura (RN-11, RN-12)`
  - `05. Upload Público (Usuário Comum - RN-11)`
  - `06. Documentos & Fila de Conferência`
  - `07. Eventos em Tempo Real (SSE)`
  - `08. Webhooks de Integração`
