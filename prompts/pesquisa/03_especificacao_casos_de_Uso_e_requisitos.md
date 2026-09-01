# 🔬 Prompt de Pesquisa 03: Consolidação da Arquitetura, Casos de Uso e Requisitos

**Ferramenta:** Gemini (Navegador)  
**Objetivo:** Consolidar os estudos de OCR (`dados sobre ocr.md`) e definições de identidade (`definicoes_identidade.md`) para gerar os documentos formais de requisitos e casos de uso de sistema.  
**Documentos Gerados no Repositório:**
- [`Especificacao_Casos_de_Uso.md`](file:///d:/DOC_Intelligence/Especificacao_Casos_de_Uso.md)
- [`Requisitos_de_Sistema.md`](file:///d:/DOC_Intelligence/Requisitos_de_Sistema.md)
- [`regras_negocio.md`](file:///d:/DOC_Intelligence/regras_negocio.md)

---

## 📝 Prompt na Íntegra (Raw)

```text
com base nos do comento acima analise o comparativo Final e Recomendações Ordenadas final, onde contem forma de implementação de OCR.  essa forma serão implementa mas será priorizada da 3.A Estrutura Ligeira de Extração Geométrica (Limitação Inferencial)
os dado extraído dos documento (identidades, comprovantes de residência, contracheques, carteiras de trabalho, laudos, procurações, contratos) que podem ser pdf(pode conter imagens dentro)  ou imagen(jpeg, jpg e png)nesse casso pode ser definido entidade template que sera um crud onde pode ser defini os campos que serão  extraido pelos OCR

para api definir OCR como sendo algo plugáveis adote padrões de projeto
o padrão Strategy (Padrão Principal) é a peça central desta arquitetura.*   Definição:  O padrão de projeto Strategy define uma família de algoritmos, encapsula cada um deles e os torna intercambiáveis 
Aplicação no OCR:  A interface principal (`InterfaceOCR`) exigirá um método comum . Cada motor de OCR  será implementado como uma estratégia separada que implementa essa interface. Isso permite isolar os detalhes de implementação de um algoritmo do código que usa ele. Além disso, permite trocar algoritmos usados dentro de um objeto durante a execução
padrão adapter (Padrão de Apoio)
Como lidaremos com bibliotecas externas de diferentes fornecedores, elas terão interfaces, retornos e métodos imcompatíveis.
Definição:  O Adapter permite a colaboração de objetos de interfaces incompatíveis. 
Aplicação no OCR: As classes de estratégia atuarão como adaptadores. Elas atuarão como um tradutor, onde a adaptação acontece dentro dos métodos sobrescritos

Fluxo do OCR 
->Analisa e identifica o template documento
-> Processar o documento 
-> Extração dos dados de acordo com template e salvo no banco
-> caso sucesso notificar sucesso, caso falhe
-> falha, um campo do template não conseguir ser identificado, será armazenado os campos restante, notificara pendencia e necessario preenchimento manual

Fluxo da APi 

deve conter um endpoint que poder vários documento, deve passado persona(que basicamente a entidade que vincula todos os documentos e os templates), um template mas e opcional já o mesmo pode ser identificado, ao envia backend adicionar a fila para processar os documento sendo processado na fila.

Na Fila (redis e celery)
Cada documento e adiciona a fila e enfileirado para ser processado, ao finaliza envia notificação usando  SSE (Server-Sent Events) , caso de sucesso avisa que os extraido com sucesso no frontend ao clicka acesso detalhes da persona.
caso falhes notificar que a documento pendente para preenchimento manual, no ao click vai para detalhes e mostra o documente pendente .
nesse ao acessa o documento mostra o documento e template(os campo para preenche manualmente) 
nesse caso preenchimento manual tera endpoint de put que passado e validado os campo de acordo o template.

endpoint para lista as persona, onde pode faler busca, filtros  por data, se contem pendencia, e pelos template utilizada um range de data(aqui pode ser crud lembrado que deletar deve ser avisado sobre as consequência adote cascade no banco )

ao acesso um detalhes de um persona, listados os documento, com seu status, data cadatro, template utilizada aplica os mesmo filtros (aqui de ser crud, mesmo caso adote cascade no banco )

ao acessar os documento mostra a imagem/pdf e os campos do template preenchido(possível editar)

adicione autenticação jwt
email e senha
 
os documento serão armazenamento no MinIO (S3) e posse gerar links seguros como na AWS

o sistema terá dois tipo usuários
-> usuário(sistema) da plataforma que criar as personas e gerar link para receber arquivos e faz preenchimento manual e acessa plataforma no gerar
-> usuário(comun) que receber o link via WhatsApp ou email acessa e envia os documentos, apenas envia documentos

o usuário(comun) acessa o link para front onde seleciona qual documento(sera carregado as opçoes de template disponível), e pode escolher a opção de anexa arquivo ou tira  foto ao tira abre a câmera do aparelho(a aplicação deve conter interface onde pequeno indicadores para tira foto corretamente foco e angulo) depois anexado os documentos, enviar sera notificado que os documento foram enviado para com sucesso.

com base nos dado acima elabore 2 documento separada um caso de use seja detalhista no fluxo e outro de requisitos
```
