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
| **13** | [`13_ajuste_mascaras_validacao_e_temas.md`](./13_ajuste_mascaras_validacao_e_temas.md) | 01/09/2026 05:45 | Máscaras de CPF/Telefone/Email, paginação, modal público e temas DaisyUI. |
| **14** | [`14_gerador_cin_sintetica_e_docs.md`](./14_gerador_cin_sintetica_e_docs.md) | 01/09/2026 06:12 | Documentação do gerador de dados e imagens sintéticas de CIN (`gerar_cin/`). |
| **15** | [`15_ajuste_navbar_temas_e_camera_mobile.md`](./15_ajuste_navbar_temas_e_camera_mobile.md) | 01/09/2026 09:15 | Temas na Navbar, notificação silenciosa de OCR e câmera mobile vertical com fallback. |
| **16** | [`16_correcao_upload_publico_persona_e_asyncpg.md`](./16_correcao_upload_publico_persona_e_asyncpg.md) | 01/09/2026 09:45 | Correção de NameError no upload público e de prepared statement no `asyncpg`. |
| **17** | [`17_documento_decisoes_arquiteturais_adr.md`](./17_documento_decisoes_arquiteturais_adr.md) | 01/09/2026 10:37 | Formatação e revisão técnica do documento de decisões arquiteturais (`O_projeto.md`). |
| **18** | [`18_correcao_menu_notificacoes_e_rota_conferencia.md`](./18_correcao_menu_notificacoes_e_rota_conferencia.md) | 01/09/2026 10:56 | Resolução da quebra visual do menu de notificações e navegação direta para conferência. |
| **19** | [`19_padronizacao_nomenclatura_documentos_e_storage.md`](./19_padronizacao_nomenclatura_documentos_e_storage.md) | 01/09/2026 11:08 | Nomenclatura `{tipo}_{persona}_{data}_{codigo_unico}.{ext}` e storage `tipo/persona/data-cod_unico`. |
| **20** | [`20_git_flow_e_versionamento_prompts.md`](./20_git_flow_e_versionamento_prompts.md) | 01/09/2026 11:19 | Adoção formal de Git Flow, commits semânticos e versionamento contínuo de prompts. |

---

## 🔬 Prompts de Pesquisa Preliminar e Concepção (`prompts/pesquisa/`)

Os prompts utilizados no navegador via Gemini (incluindo o recurso *Deep Research*) para elicitação de requisitos, estudo de motores OCR e análise do Decreto da CIN estão catalogados no diretório [`prompts/pesquisa/`](./pesquisa/):

| # | Arquivo | Tópico Principal / Escopo |
| :-: | :--- | :--- |
| **P1** | [`pesquisa/01_deep_research_ocr_open_source.md`](./pesquisa/01_deep_research_ocr_open_source.md) | Deep research de motores OCR open source (EasyOCR, Tesseract, etc.) para documentos brasileiros. |
| **P2** | [`pesquisa/02_definicoes_documento_identidade_cin.md`](./pesquisa/02_definicoes_documento_identidade_cin.md) | Pesquisa técnica e legal das especificações da nova Carteira de Identidade Nacional (CIN). |
| **P3** | [`pesquisa/03_especificacao_casos_de_Uso_e_requisitos.md`](./pesquisa/03_especificacao_casos_de_Uso_e_requisitos.md) | Consolidação arquitetural de requisitos, casos de uso, Strategy + Adapter, MinIO S3, SSE e Celery. |

---

*Todos os arquivos acima estão devidamente commitados e versionados no repositório.*