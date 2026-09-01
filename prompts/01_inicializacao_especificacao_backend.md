# Prompt 01: Inicialização e Especificação do Backend

**Data/Hora:** 2026-08-31T23:35:12Z (20:35:12 -03:00)  
**Contexto:** Definição inicial do projeto e solicitação de planejamento via `/grill-me`.

## Prompt na Íntegra (Raw)

```text
/grill-me analise o documento D:\DOC_Intelligence Requisitos_de_Sistema, ocr-deep-research, Especificacao_Casos_de_Uso, definicoes_doc_identidade criar pasta backend inicialmente desenvolver api 
onde receber documentos(pdf/pdf com uma imagem dentro, jpeg, peg, png) e extrair os dados do documento atual fazer pelo meno para documento de identidade CIN

para os arquivos utilize uma instancia do minio para simular bucketS3, quando falhar retorna a o link da imagem,
configura sistema de notificação para suceso ou falha ao processar as imagens.

padronizar as nomeclatura dos nome do documento para salva,torne a nomeclatura de custumizacao.
elabore uma forma de atrelar o usuario logado os dados que estao sendo salvos um forma saber que aquele usuario que registre o envio do documento. 
cada documento sera salva numa especie de workspace ou persona onde ficar os documentos          

como o objetivo é poder plugar e desplugar motores de OCR sem alterar as camadas superiores (garantindo que o código não fique acoplado a uma biblioteca específica como EasyOCR, Tesseract ou Google Cloud Vision)
```\n