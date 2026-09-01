# **Especificação de Casos de Uso \- Plataforma de Onboarding e OCR**

## **1\. Atores do Sistema**

* **Usuário Sistema (Operador/Administrador/Conferente):** Acessa a plataforma interna. Responsável por criar Personas, cadastrar templates (CRUD), gerar links de coleta, monitorar o dashboard, acessar a fila de conferência, gerenciar pendências e realizar a revisão/preenchimento manual de dados com baixa confiança ou não extraídos pelo OCR.  
* **Usuário Comum (Cliente final):** Acessa a interface externa via link recebido (WhatsApp/E-mail). Responsável apenas por enviar as fotos ou arquivos de seus documentos.  
* **Sistema (Workers/Filas):** Ator sistêmico responsável pelo processamento assíncrono, rasterização de PDFs, higienização de imagens (OpenCV) e extração de texto (EasyOCR).

## **2\. Caso de Uso: UC01 \- Coleta e Envio de Documentos**

**Ator Principal:** Usuário Comum

**Resumo:** O usuário acessa o link seguro, seleciona o tipo de documento e realiza o upload ou captura da foto.

**Fluxo Principal:**

1. O Usuário Comum clica no link seguro recebido.  
2. O sistema exibe uma interface Web contendo as opções de templates de documentos disponíveis para aquela Persona.  
3. O usuário seleciona o documento que deseja enviar (ex: CNH, Comprovante de Residência).  
4. O sistema oferece as opções: "Anexar Arquivo" (PDF, JPG, PNG) ou "Tirar Foto".  
5. O usuário escolhe "Tirar Foto".  
6. O sistema abre a interface da câmera com pequenos indicadores visuais na tela (guias de foco, alinhamento e ângulo).  
7. O usuário captura a imagem e confirma o envio.  
8. O sistema empacota a imagem junto com o ID da Persona e o ID do Template, enviando para a API.  
9. A API retorna uma notificação de sucesso: "Documentos enviados com sucesso".  
10. O caso de uso é encerrado para o Usuário Comum.

## **3\. Caso de Uso: UC02 \- Processamento e Extração via OCR**

**Ator Principal:** Sistema (Worker/Celery)

**Resumo:** A API recebe o documento, enfileira, aplica os padrões Strategy/Adapter e tenta extrair os dados baseados no template.

**Fluxo Principal (Sucesso Total \- Alta Confiança):**

1. O *Endpoint* da API recebe o payload contendo o documento, a Persona e (opcionalmente) o Template.  
2. A API salva o arquivo bruto no **MinIO (S3)** e adiciona a tarefa na fila do **Redis**.  
3. O **Celery Worker** consome a tarefa da fila.  
4. Se o arquivo for PDF, o sistema o converte para imagem (rasterização).  
5. O Worker analisa e identifica o template do documento.  
6. O sistema invoca a InterfaceOCR (Padrão *Strategy*).  
7. A classe concreta atua como *Adapter*, compatibilizando as bibliotecas externas (OpenCV \+ EasyOCR).  
8. O sistema extrai os dados conforme os campos definidos no Template e avalia o **nível de confiança (confidence score)** da extração.  
9. Todos os campos são extraídos com alto nível de confiança (acima do limiar configurado) e salvos no banco de dados vinculados à Persona com status "Pronto".  
10. O sistema dispara uma notificação via **SSE (Server-Sent Events)** para o front-end avisando do sucesso.

**Fluxo Alternativo A (Falha Parcial ou Baixa Confiança \- Fila de Conferência):**

1. (Passos 1 a 7 iguais ao Fluxo Principal).  
2. O sistema falha em identificar um ou mais campos, **OU** a extração retorna um nível de confiança baixo (suspeita de erro da máquina).  
3. O sistema armazena no banco de dados os campos extraídos, sinalizando quais possuem baixa confiança ou estão em branco.  
4. O status do documento é marcado como "Pendente/Para Revisão".  
5. O sistema direciona o documento para a **Fila de Conferência** e dispara um evento **SSE** alertando os Conferentes.

## **4\. Caso de Uso: UC03 \- Fila de Conferência e Intervenção Humana (Com Locking)**

**Ator Principal:** Usuário Sistema (Conferente)

**Resumo:** O conferente acessa a fila de documentos retidos por baixa confiança/falha, assume a revisão do documento (bloqueando-o para outros) e corrige os dados.

**Fluxo Principal:**

1. O Usuário Sistema acessa o módulo "Fila de Conferência" no dashboard.  
2. O sistema lista todos os documentos com status "Pendente/Para Revisão".  
3. O usuário clica em um documento específico para iniciar a revisão.  
4. O sistema aplica um **Lock (Bloqueio Pessimista)** no documento, vinculando-o ao usuário atual, e altera o status visual para "Em Análise por \[Nome do Usuário\]".  
5. O sistema exibe a interface de conferência: visualização lado a lado (imagem/PDF original na esquerda e o formulário preenchido na direita).  
6. Os campos com baixa confiança gerados pela máquina são destacados visualmente (ex: cor amarela/vermelha).  
7. O usuário compara os dados com a imagem, corrige os eventuais erros e preenche o que faltou.  
8. O usuário clica em "Aprovar Documento".  
9. O sistema faz uma requisição PUT, valida os campos e salva os dados definitivos.  
10. O sistema libera o *Lock* do documento e atualiza seu status para "Pronto", removendo-o da fila de conferência.

**Fluxo Alternativo A (Conflito de Concorrência na Fila):**

1. O usuário tenta acessar um documento na Fila de Conferência que já está sendo revisado por outro conferente (Lock ativo).  
2. O sistema bloqueia o acesso à edição.  
3. O sistema exibe um alerta: "Este documento já está em edição pelo usuário \[Nome do Usuário\]".  
4. O usuário é redirecionado de volta para a lista da Fila de Conferência.

**Fluxo Alternativo B (Abandono de Revisão / Timeout do Lock):**

1. O usuário abre um documento, ativando o Lock, mas fecha o navegador ou perde a conexão antes de aprovar.  
2. O sistema, através de um TTL (Time-To-Live) no Redis ou verificação de inatividade, identifica que o tempo de revisão expirou.  
3. O sistema remove o Lock automaticamente.  
4. O documento volta a ficar disponível na Fila de Conferência para outros usuários.

## **5\. Caso de Uso: UC04 \- Gestão de Personas e Documentos (CRUD)**

**Ator Principal:** Usuário Sistema

**Resumo:** Manutenção das entidades principais, listagem e aplicação de filtros.

**Fluxo Principal (Listagem e Filtros):**

1. O usuário acessa a tela de listagem de Personas.  
2. O usuário aplica filtros: "Range de data", "Com pendência na fila", "Por template utilizado", "Aprovados".  
3. O sistema exibe os resultados correspondentes.

**Fluxo Alternativo (Exclusão com Cascade):**

1. O usuário seleciona uma Persona (ou documento) e clica em excluir.  
2. O sistema exibe um alerta informando que a ação é irreversível e afetará os dados no banco e no MinIO (Cascade).  
3. O usuário confirma.  
4. O sistema executa o *Delete Cascade*, limpando todos os rastros associados.