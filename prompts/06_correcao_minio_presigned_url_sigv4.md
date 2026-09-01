# Prompt 06: Resolução de SignatureDoesNotMatch no MinIO SigV4 e Listagem de Imagens

**Data/Hora:** 2026-09-01T03:30:55Z (00:30:55 -03:00)  
**Contexto:** Diagnóstico de falha de assinatura na visualização de presigned URLs no MinIO.

## Prompt na Íntegra (Raw)

```text
curl --location 'http://localhost:8000/api/v1/documents/5734cee6-16f4-4199-bbc5-c2cfc9a96edd' \
--header 'Authorization: Bearer <JWT_TOKEN>'

  "approved_by_user_id": "af9d1e4d-fa3c-4d51-aacd-f87f1ed6f9d6",
    "approved_at": "2026-09-01T03:21:13.469995Z",
    "preview_url": "http://localhost:9000/doc-intelligence-storage/personas/47089979-ff1c-4a2c-8a8e-75684a325c57/CIN/2026/09/5734cee6-16f4-4199-bbc5-c2cfc9a96edd_cin_10_camila_ferreira_silva_verso.png?..."
}


a url de visuaizaçâo gera não esta acessivel, exencial para leitura,  edev ser possivel todos os cdumento enviado nesse seria lista analise para applica o ajuste
```\n