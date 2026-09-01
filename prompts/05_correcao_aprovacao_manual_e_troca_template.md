# Prompt 05: Conferência Manual e Reclassificação de Template (RN-10)

**Data/Hora:** 2026-09-01T03:24:03Z (00:24:03 -03:00)  
**Contexto:** Correção do fluxo de aprovação manual e permissão de troca de template para o operador.

## Prompt na Íntegra (Raw)

```text
curl --location --request PUT 'http://localhost:8000/api/v1/documents/5734cee6-16f4-4199-bbc5-c2cfc9a96edd/review' \
--header 'Authorization: Bearer <JWT_TOKEN>' \
--header 'Content-Type: application/json' \
--data '{
  "corrected_data": {
    "cpf": "123.456.789-09",
    "rg_numero": "23233232323232",
    "nome_completo": "CARLOS ALBERTO FERREIRA",
    "data_nascimento": "15/05/1990",
    "naturalidade": "SÃO PAULO",
    "nacionalidade": "BRASILEIRA",
    "data_validade": "15/05/2034"
  },
  "notes": "Campos conferidos e aprovados manualmente pelo operador."
}'

na provacao manual passei seguinte valores mas memsmo assim os valores esato como pendendo no retorno, aprovacao manu e basicamento preencguend dados manualmentoo olahanod para imagen e deve ser possivel alterar o tipo template caso seja inferido errado
```\n