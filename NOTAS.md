# Notas do MVP

## O que já está pronto
- Site FastAPI com busca local.
- Banco SQLite.
- Seed de dados para demonstração.
- Adaptador inicial do PNCP.
- Robô `fetcher.py` para ingestão automática.

## O que falta para produção
- Confirmar endpoint de consulta mais adequado no Swagger atual do PNCP.
- Refinar parser dos campos vindos do PNCP.
- Criar páginas estáticas por categoria para SEO programático.
- Configurar hospedagem real e Search Console.
- Instalar AdSense depois que houver conteúdo indexado.

## Sugestão operacional
- Rodar `fetcher.py` 2x ao dia no começo.
- Monitorar quantos registros entram por categoria.
- Só depois ampliar para portais fora do PNCP.
