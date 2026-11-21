# Radar de Preços — plano gratuito

Site estático GitHub Pages + GitHub Actions + SerpApi Google Shopping.

## Segurança da cota

- Plano gratuito SerpApi: 250 buscas por ciclo mensal (verifique no painel da sua conta).
- Script limita o uso total da conta a **190 buscas por ciclo**, deixando pelo menos **60 buscas de reserva**.
- Antes de **cada** consulta ao Google Shopping, usa a API gratuita `account.json` para verificar plano, uso e saldo. Se a verificação falhar, **não faz buscas**.
- Faz buscas a cada 2 dias (`17 10 */2 * *`, UTC), máximo de 16 execuções em meses de 31 dias.
- O projeto permite no máximo 11 produtos automáticos, ou até 176 pesquisas em um mês de 31 dias quando a cota está integralmente disponível. Inicia com 5 produtos (até 80 pesquisas por mês). Se executar manualmente, cada execução pode usar até uma busca por produto e consume do mesmo limite total de 190.
- A cota é pelo ciclo de assinatura da API, **não necessariamente pelo mês calendário**. A API de conta dita o saldo real.
- Os custos são zero **somente se você permanecer no plano gratuito**, sem ativar renovação antecipada/upgrade pago. Confira isso no painel da SerpApi.

## Ativação

1. Crie um repositório público no GitHub e suba estes arquivos mantendo as pastas.
2. Settings > Secrets and variables > Actions > New repository secret: nome `SERPAPI_KEY`, valor da chave que você obteve diretamente no painel da SerpApi. **Nunca coloque a chave no HTML nem envie-a por chat.**
3. Ative GitHub Actions; execute manualmente `Atualizar preços (cota grátis)` uma vez para conferir.
4. Settings > Pages > Build and deployment > Deploy from a branch: selecione `main` e `/ (root)`.
5. Abra `https://USUARIO.github.io/NOME-REPO/` após a publicação.

## Adicionar produtos

- No site, o botão "Cadastrar produto" adiciona um produto **somente ao navegador atual** para anotações e comparações manuais.
- Para **coleta automática**, adicione também uma entrada em `products.json` no repositório, com `id`, `name`, `model` (código exato do modelo) e `query` (busca específica). Para aparecer automaticamente no site em novos dispositivos, adicione entrada correspondente à lista `seeds` em `index.html` usando **o mesmo `id`**. Uma futura versão pode sincronizar o catálogo por JSON sem alterar o código.
- Não ultrapasse 11 produtos de coleta automática. O script bloqueia acima disso; ele também protege a cota mensal efetiva.
- Resultados da API são preços de anúncios do Google Shopping, não preço final no carrinho. Frete, cupons, estoque e compatibilidade do modelo precisam de conferência. A correspondência é filtrada pelo código de modelo, mas pode ter falsos positivos; revise preços antes de decidir.
- Os dados públicos são armazenados em `data/prices.json`; o histórico anterior à primeira coleta não é inventado.
