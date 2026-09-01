# Prompt 04: Correção de Integridade do Schema (Remoção de workspace_id no MVP)

**Data/Hora:** 2026-09-01T02:54:25Z (23:54:25 -03:00)  
**Contexto:** Correção do erro `NotNullViolationError` na coluna `workspace_id` de `personas`.

## Prompt na Íntegra (Raw)

```text
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.NotNullViolationError'>: null value in column "workspace_id" of relation "personas" violates not-null constraint

DETAIL:  Failing row contains (null, Carlos Alberto Ferreira, carlos.ferreira@example.com, 12345678909, +5511999998888, PENDING, ["CIN"], {"origem": "portal_web", "departamento": "RH"}, 24924251-99cc-4e9a-990a-9c8c9f8aa2d2, 2026-09-01 02:48:46.821012+00, 2026-09-01 02:48:46.821015+00).

workspace_id, foi  feitas as alteraçoes no codigo mas não reflito no bando de dados o fluxo que necessida workspace_id ainda existe na tabela, analise as migrations e dados relacionado entidade para fazer correção
```\n