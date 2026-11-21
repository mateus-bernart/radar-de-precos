# Radar de Preços

Aplicação pessoal estática, com catálogo público em `products.json` e histórico incremental em `data/prices.json`. A cópia antiga `prices.json` é preservada e importada pelo coletor sem apagar dados.

## Publicação e primeira coleta

1. Em https://github.com/mateus-bernart/radar-de-precos/settings/pages selecione **Source: GitHub Actions**.
2. O Secret `SERPAPI_KEY` deve existir em Actions (nunca no frontend).
3. Abra https://github.com/mateus-bernart/radar-de-precos/actions/workflows/prices.yml e selecione **Run workflow**, branch `main`.
4. Verifique os jobs de coleta e publicação. O endereço esperado é https://mateus-bernart.github.io/radar-de-precos/ . Somente uma execução e uma visita bem-sucedidas confirmam funcionamento.

O workflow publica seu próprio artefato com `deploy-pages`; portanto não depende de um commit feito com GITHUB_TOKEN disparar outro workflow. Pushes publicam sem consumir a API. Execuções manuais e agendadas compartilham a mesma trava de concorrência. O cron diário verifica o intervalo real de 48 horas por produto. Nos dias 26, 27 e 30/11/2026 admite uma coleta por dia em São Paulo, respeitando saldo.

## Plano gratuito e proteção

Conferido em 21/11/2026: https://serpapi.com/pricing anuncia Free, US$ 0, 250 buscas/mês; https://serpapi.com/account-api informa que Account API é gratuita e documenta os campos de plano, uso, saldo e renovação.

Antes de cada busca o script exige conta ativa, identificação explícita do plano Free, preço zero numérico, franquia de exatamente 250, ciclo válido e saldos inteiros coerentes. Campos ausentes ou formatos desconhecidos bloqueiam a busca. Teto 190, reserva 60. O contador local também protege contra atraso na atualização do saldo da API. No máximo 11 produtos; uma busca por produto a cada 48 horas, inclusive em execuções manuais. Consultas feitas por outros sistemas na mesma chave aparecem no saldo real; evite usar a mesma chave em coletores concorrentes externos.

A interface mostra somente os campos públicos permitidos de consumo; respostas completas da conta podem conter chave e email e nunca são salvas ou registradas. Erros são redigidos sem URLs nem mensagens brutas da API. Nenhuma contratação, renovação paga ou cobrança é configurada.

## Catálogo e dados locais

Os cinco produtos publicados aparecem em todos os aparelhos. Cadastro e edição feitos no site ficam no navegador. **Preparar catálogo automático** copia o JSON e abre o editor autenticado do GitHub: substitua o conteúdo de `products.json` pelo catálogo copiado e confirme o commit. Não há token no site. Até 11 produtos; mantenha IDs estáveis e código de modelo exato. Para excluir produto automático, remova sua entrada no GitHub; seu histórico permanece. Excluir um produto local remove seus registros locais após confirmação.

O Samsung S30GD existe em tamanhos diferentes: a correspondência exige 24 polegadas. Código brasileiro: LS24D300GALMZD. O AOC 24G4 usa a variante brasileira 24G4/P, sem misturar com 24G4E. Fontes oficiais das especificações constam no campo `url` do catálogo. Q27G4F IPS plano nunca corresponde a CQ27G4F.

## Histórico e limitações

Os preços são anúncios encontrados no Google Shopping. Modelo exato reduz erros, mas não confirma estoque, vendedor ou preço no carrinho. Nenhum histórico retroativo é inventado. Frete desconhecido fica nulo e é indicado na interface. Usados, seminovos, cupons e confirmação de carrinho podem ser anotados manualmente.

A referência habitual usa mediana por loja/dia, sem cupons e sem preços marcados como excepcionais. Valores fora de 50% a 150% da mediana são separados da referência, preservados no histórico. Essa heurística não prova que uma oferta é incorreta. Comparações podem misturar fretes conhecidos e desconhecidos e são indicativas; verifique as condições antes de comprar.

A janela BF é 27 a 30/11/2026; referência anterior usa somente datas anteriores a 27/11, nunca a categoria livre do registro. Os filtros de 7, 15, 30, 90 e 365 dias não criam dados ausentes. Backup JSON e CSV incluem histórico público e local. Backups importados são validados e substituem apenas os dados locais.

## Testes

`python3 -m unittest discover -s tests -v`

Valida plano, saldo, reserva, falhas, intervalo efetivo, datas especiais, atraso da Account API, correspondência de modelos, limite de produtos e preservação dos registros parciais.
