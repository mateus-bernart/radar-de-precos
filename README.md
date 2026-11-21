# Radar de Preços

Aplicação pessoal para acompanhar preços, comparar ofertas e construir um histórico para a Black Friday.

**[Acessar o site](https://mateus-bernart.github.io/radar-de-precos/)** — funciona no celular e no computador.

## Como funciona

- Consulta preços automaticamente pelo GitHub Actions e pela SerpApi, mesmo com o site fechado.
- O agendamento verifica diariamente quais produtos completaram o intervalo mínimo de 48 horas desde a última consulta.
- Mostra fotos, preço-alvo, histórico, gráficos e comparação de preços.
- Aceita somente links diretos de Mercado Livre, Amazon Brasil, Shopee, KaBuM! e Terabyte Shop.
- Permite registrar ofertas manualmente e exportar CSV ou backups JSON.

## Para usar

1. Abra o site e consulte os produtos acompanhados.
2. Clique no botão do menor preço quando houver uma oferta permitida.
3. Use **Histórico e comparar** para acompanhar a evolução dos preços.

Os cinco monitores do catálogo já estão na coleta automática. Novos produtos cadastrados no site ficam apenas no navegador até você usar **Preparar catálogo automático** e salvar o catálogo no GitHub.

## Informações importantes

Os valores são preços anunciados: frete, estoque, cupons e preço final devem ser conferidos na loja. Quando não houver um link direto das lojas permitidas, o site informa que não há oferta disponível. O histórico começa nas coletas realizadas; preços anteriores não são inventados.

O projeto usa GitHub Pages, GitHub Actions e o plano gratuito da SerpApi, com teto de segurança de 190 buscas por ciclo e reserva de 60. A chave da API fica nos Secrets do GitHub, fora do site.

Para detalhes de configuração e manutenção, consulte [LEIA-ME.md](LEIA-ME.md).
