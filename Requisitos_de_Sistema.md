# **Documento de Requisitos de Sistema (DRS)**

## **1\. Visão Geral**

O sistema consiste em uma plataforma dividida entre uma interface interna de gestão (para operadores/conferentes) e uma interface externa de coleta de dados (para clientes finais). O núcleo técnico do sistema utiliza filas de processamento assíncrono para extração de dados (OCR com OpenCV e EasyOCR) baseada em templates. Documentos com baixa confiança na extração são retidos em uma fila com controle de concorrência para revisão humana.

## **2\. Requisitos Funcionais (RF)**

| Identificador | Nome | Descrição |
| :---- | :---- | :---- |
| **RF01** | **Autenticação JWT** | O sistema deve permitir o login do Usuário Sistema via e-mail e senha, gerando e validando tokens JWT. |
| **RF02** | **CRUD de Templates** | O sistema deve possuir um CRUD para criação de Entidades Template, definindo os campos exatos que o OCR ou o operador deverão extrair (ex: CNH, RG). |
| **RF03** | **CRUD de Personas** | O sistema deve permitir o gerenciamento de Personas (entidade agregadora que vincula documentos e templates). |
| **RF04** | **Geração de Link Seguro** | A plataforma deve permitir ao Usuário Sistema gerar um link de acesso para o Usuário Comum enviar seus documentos. |
| **RF05** | **Upload Multimodal** | A interface do Usuário Comum deve aceitar arquivos PDF ou imagens nativas (JPEG, JPG, PNG). |
| **RF06** | **Interface de Câmera Orientada** | Ao optar por tirar foto, o front-end deve exibir indicadores visuais (guias de foco e ângulo). |
| **RF07** | **Endpoint de Recepção e Fila** | A API deve receber os documentos, a Persona e o template (opcional), adicionando a carga à fila de processamento (Celery/Redis). |
| **RF08** | **Fila de Conferência** | O sistema deve possuir uma interface dedicada ("Fila de Conferência") para listar documentos cuja extração falhou ou retornou baixa confiança, aguardando revisão humana. |
| **RF09** | **Controle de Concorrência (Lock)** | O sistema deve implementar um mecanismo de lock (bloqueio de registro) para impedir que duas pessoas da equipe de atendimento editem/revisem o mesmo documento simultaneamente. |
| **RF10** | **Visualização Lado a Lado** | A tela de conferência deve renderizar o documento original (imagem/PDF) lado a lado com o formulário de dados extraídos para facilitar a comparação. |
| **RF11** | **Endpoint de Aprovação/Edição** | O sistema deve conter um endpoint PUT para salvar a revisão manual. Este endpoint validará os campos, liberará o *lock* de concorrência e marcará o documento como "Pronto". |
| **RF12** | **Filtros e Buscas** | A listagem de Personas e documentos deve permitir filtros por: Range de data, Status (Pronto, Em Revisão, Pendente) e Templates. |

## **3\. Requisitos Não Funcionais (RNF)**

| Identificador | Nome | Descrição |
| :---- | :---- | :---- |
| **RNF01** | **Arquitetura de OCR Plugável** | A implementação do OCR adotará o **Padrão Strategy**. O sistema terá uma InterfaceOCR central e os motores serão estratégias. |
| **RNF02** | **Padrão Adapter para Bibliotecas** | As classes de estratégia atuarão como **Adapters**, traduzindo as interfaces e retornos de bibliotecas externas (ex: OpenCV, EasyOCR). |
| **RNF03** | **Motor OCR \- Estrutura Ligeira** | Prioridade para técnica de "Estrutura Ligeira de Extração Geométrica" (Limitação Inferencial) usando OpenCV para higienização e EasyOCR/Tesseract para leitura. |
| **RNF04** | **Processamento Assíncrono** | O fluxo de OCR deve ocorrer de forma assíncrona, utilizando **Redis** como *broker* de mensageria e **Celery** para execução das tarefas (Workers). |
| **RNF05** | **Notificações Real-Time (SSE)** | A comunicação de sucesso ou direcionamento para a fila de conferência para o front-end será via **Server-Sent Events (SSE)**. |
| **RNF06** | **Armazenamento de Arquivos** | Documentos enviados devem ser salvos de forma segura em bucket do **MinIO (S3)**, acessados via links seguros da API. |
| **RNF07** | **Gerenciamento do Mecanismo de Lock** | O lock pessimista da Fila de Conferência deve ser preferencialmente gerenciado via **Redis** com definição de TTL (Time-To-Live), evitando que um documento fique bloqueado eternamente caso o usuário feche o navegador. |
| **RNF08** | **Exclusão em Cascata (Database)** | A exclusão de Personas/Templates adotará regras de *Cascade* no banco e remoção no MinIO, exigindo alerta prévio. |

## **4\. Regras de Negócio (RN)**

| Identificador | Nome | Descrição |
| :---- | :---- | :---- |
| **RN01** | **Retenção por Baixa Confiança ou Falha** | O sistema NUNCA deve aprovar automaticamente um documento se o motor de IA/OCR não identificar um campo exigido ou se o índice de confiança (confidence score) da extração for inferior ao limiar seguro definido. Estes devem ir obrigatoriamente para a Fila de Conferência. |
| **RN02** | **Prevenção de Edição Dupla** | Um documento em status "Em Análise por \[Usuário\]" não pode ter seus dados submetidos ou alterados por outro usuário. O acesso à edição deve ser estritamente bloqueado. |
| **RN03** | **Identificação Dinâmica de Template** | Se o Usuário Comum enviar um documento sem especificar o template, o Worker deduzirá o template na primeira etapa da análise. |
| **RN04** | **Isolamento de Usuário Comum** | O Usuário Comum não possui acesso à listagem de Personas, filas ou dashboard; acesso efêmero e restrito ao link recebido para envio. |

