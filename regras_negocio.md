# **Documento de Regras de Negócio (RN)**

**Sistema de Onboarding e Extração OCR**

Este documento descreve as regras, políticas, validações e restrições de domínio que norteiam o funcionamento da plataforma de coleta e processamento de documentos. Estas regras devem ser implementadas no *backend* para garantir a integridade dos dados e o cumprimento legal (LGPD).

## **1\. Regras de Processamento, Extração e Qualidade (OCR)**

| Identificador | Nome | Descrição Detalhada |
| :---- | :---- | :---- |
| **RN-01** | **Retenção Obrigatória por Baixa Confiança** | O sistema **nunca** deve aprovar automaticamente um documento se o *confidence score* (índice de confiança da extração retornado pelo EasyOCR) de qualquer **campo obrigatório** for inferior a **85%**. Documentos que caiam nessa condição, ou onde um campo obrigatório retorne vazio (nulo), devem ser compulsoriamente movidos para o status "Pendente" na Fila de Conferência. |
| **RN-02** | **Dedução de Template e Fallback** | Se o Usuário Comum submeter um documento sem especificar o template, o motor de visão (ex: YOLO/OpenCV) deve tentar classificar a imagem. Se a confiança da classificação do template for inferior a **90%**, o sistema não deve tentar extrair os dados. O documento deve ir para a Fila de Conferência com o status "Template Não Identificado", forçando o humano a classificar antes da extração. |
| **RN-03** | **Normalização Ortográfica (Fuzzy Matching)** | Para campos textuais como "Nomes de Cidades" (Naturalidade), o sistema aplicará a *Distância de Levenshtein* (ex: via biblioteca RapidFuzz). Se a similaridade com a base oficial do IBGE for **entre 80% e 99%**, o sistema **corrige automaticamente** (ex: "S4O PAU10" vira "SÃO PAULO"). Se for menor que 80%, a palavra original é mantida e sinalizada com alerta visual (amarelo) para o conferente. |
| **RN-04** | **Validação Criptográfica de Identificadores** | Dados numéricos com padrão verificador (CPF, CNPJ, RENAVAM) devem ser validados via cálculo matemático (módulo 11, via biblioteca *validate-docbr*). **Regra de Ouro:** Se o módulo matemático falhar, o dado é considerado INVÁLIDO sumariamente. A alta confiança visual do OCR é ignorada nestes casos, e o documento vai para revisão humana. |
| **RN-05** | **Conformidade de Leiaute (RG vs. CIN)** | A exigência de campos depende do template. \- **Template CIN (Nova Identidade):** O sistema não deve procurar ou exigir os campos "RG Estadual", "Filiação" e "Sexo", pois não existem na via impressa. O CPF é a chave primária. \- **Template RG Antigo:** Os campos de Filiação e RG Estadual são obrigatórios. |
| **RN-06** | **Padronização de Rasterização (PDFs)** | Se o arquivo de entrada for um PDF, a sua conversão em imagem (rasterização via *pypdfium2*) deve ocorrer estritamente a **300 DPI**. Resoluções inferiores não garantem a leitura das microletras dos documentos de identidade e devem ser rejeitadas ou redimensionadas pelo *backend*. |

## **2\. Regras de Operação e Intervenção Humana (Fila)**

| Identificador | Nome | Descrição Detalhada |
| :---- | :---- | :---- |
| **RN-07** | **Exclusividade de Revisão (Locking Pessimista)** | Um documento em status "Em Análise" só pode ser visualizado em modo de edição por um (1) único Usuário Sistema simultaneamente. O bloqueio é atrelado ao ID do Usuário e ao ID da Sessão. Tentativas de acesso concorrente devem retornar erro HTTP 409 (Conflict). |
| **RN-08** | **Expiração de Bloqueio (TTL do Lock)** | O bloqueio de edição na fila de conferência terá um *Time-To-Live* (TTL) cravado no Redis de **10 minutos**. Aos 8 minutos, o frontend deve alertar o usuário. Passados os 10 minutos sem *commit* (salvamento), o bloqueio é derrubado, a edição em andamento é descartada, e o documento volta ao status "Pendente" para a equipe. |
| **RN-09** | **Rejeição Definitiva de Qualidade** | Se a imagem submetida estiver borrada a ponto de ser ilegível para o humano e para a máquina, o Conferente pode acionar o botão "Rejeitar Imagem". Isso encerra o ciclo deste arquivo e engatilha um evento (notificação via webhook/SSE) para alertar o Usuário Comum a enviar uma nova foto nítida. |
| **RN-10** | **Imutabilidade e Auditoria** | Após um Conferente marcar um documento como "Pronto" (salvando os dados editados), o registro torna-se imutável. O sistema deve gravar no banco de dados a trilha de auditoria: approved\_by (ID do conferente) e approved\_at (Timestamp). Qualquer alteração posterior exige privilégios de Administrador. |

## **3\. Regras de Acesso, Segurança e LGPD**

| Identificador | Nome | Descrição Detalhada |
| :---- | :---- | :---- |
| **RN-11** | **Isolamento de Perspectiva do Cliente** | O Usuário Comum acessa a aplicação através de um *token* de sessão JWT efêmero embutido no link. Este token limita-se à rota de POST /upload vinculada apenas ao seu ID de Persona. Tentar acessar listagens (GET /personas) resultará em HTTP 403 (Forbidden). |
| **RN-12** | **Expiração de Link de Coleta** | Os links de coleta enviados (WhatsApp/E-mail) expiram em **48 horas**. Um link expirado deve renderizar uma tela amigável no *frontend* informando a perda de validade e orientando o usuário a solicitar um novo link ao atendimento. |
| **RN-13** | **Remoção Segura e em Cascata (Right to be Forgotten)** | A exclusão de uma Persona obriga a execução de um *Hard Delete*. O sistema deve apagar os metadados do banco relacional (Cascade) e emitir um comando irreversível de exclusão de objetos no *bucket* do MinIO. Não deve haver *Soft Delete* (deleção lógica) de imagens de documentos para conformidade estrita com a LGPD. |
| **RN-14** | **Mascaramento de Dados Sensíveis (Logs)** | Dados PII (Personally Identifiable Information) extraídos pelo OCR, como Nomes, CPF, Filiação e RG, **não podem** ser impressos em arquivos de log da aplicação (ex: logs do Celery ou FastAPI). Os logs devem referenciar apenas IDs de transação e status (ex: "Extração concluída para doc\_id=123"). |
| **RN-15** | **Completude da Persona** | Uma "Persona" só é considerada com o status "Onboarding Concluído" se possuir, no mínimo, todos os documentos listados como obrigatórios no momento de sua criação (ex: 1 Documento de Identificação \+ 1 Comprovante de Residência) devidamente processados e com status "Pronto". |

