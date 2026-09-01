# 📜 Registro Cronológico de Prompts do Projeto DOC_Intelligence

Este diretório contém o registro integral e cronológico de todos os prompts de comando fornecidos durante o desenvolvimento do ecossistema **DOC_Intelligence**.

---

## 📑 Tabela de Rastreabilidade Cronológica

| # | Arquivo | Data / Hora (UTC-3) | Tópico Principal / Escopo |
| :-: | :--- | :--- | :--- |
| **01** | [`01_inicializacao_especificacao_backend.md`](./01_inicializacao_especificacao_backend.md) | 31/08/2026 20:35 | Especificação inicial, Clean Architecture, MinIO S3 e OCR CIN/RG. |
| **02** | [`02_regras_negocio.md`](./02_regras_negocio.md) | 31/08/2026 21:18 | Incorporação formal das 15 Regras de Negócio (RN-01 a RN-15). |
| **03** | [`03_postman_collection.md`](./03_postman_collection.md) | 31/08/2026 22:04 | Criação de Postman Collection e Environment com variáveis completas. |
| **04** | [`04_ajuste_schema_remocao_workspace_id.md`](./04_ajuste_schema_remocao_workspace_id.md) | 31/08/2026 23:54 | Resolução de `NotNullViolationError` via migração Alembic para o modelo MVP. |
| **05** | [`05_correcao_aprovacao_manual_e_troca_template.md`](./05_correcao_aprovacao_manual_e_troca_template.md) | 01/09/2026 00:24 | Correção de aprovação manual e reclassificação de template (RN-10). |
| **06** | [`06_correcao_minio_presigned_url_sigv4.md`](./06_correcao_minio_presigned_url_sigv4.md) | 01/09/2026 00:30 | Correção do cálculo SigV4 no MinIO e listagem em lote de `preview_url`. |
| **07** | [`07_mock_ocr_engine_ratio_80_20.md`](./07_mock_ocr_engine_ratio_80_20.md) | 01/09/2026 00:46 | Motor de OCR Mockado com razão determinística 80% READY / 20% NEEDS_REVIEW. |
| **08** | [`08_git_flow_e_inicializacao_repositorio.md`](./08_git_flow_e_inicializacao_repositorio.md) | 01/09/2026 01:03 | Inicialização do Git Flow (`main`, `develop`, feature branches e tags). |
| **09** | [`09_frontend_angular_21_signals_daisyui.md`](./09_frontend_angular_21_signals_daisyui.md) | 01/09/2026 01:23 | Especificação do frontend Angular 21 Standalone + Signals + DaisyUI. |
| **10** | [`10_portal_publico_camera_guiada_mobile.md`](./10_portal_publico_camera_guiada_mobile.md) | 01/09/2026 01:33 | Refinamento do portal público com câmera ao vivo e retícula de enquadramento. |
| **11** | [`11_docker_frontend_e_ambientes_prod_dev.md`](./11_docker_frontend_e_ambientes_prod_dev.md) | 01/09/2026 02:09 | Dockerfile multi-stage Nginx, ambientes Prod/Dev e Docker Compose unificado. |
| **12** | [`12_criacao_pasta_prompts_versionamento.md`](./12_criacao_pasta_prompts_versionamento.md) | 01/09/2026 02:18 | Solicitação de criação e versionamento da pasta `prompts/`. |

---

*Todos os arquivos acima estão devidamente commitados e versionados no repositório.*\n