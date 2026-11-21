"""Consulta Google Shopping com limite conservador do plano gratuito SerpApi.

Executa em GitHub Actions. Falha fechada: se nao puder conferir a conta,
nao chama a API de busca. Uma busca por produto por execucao.
"""
import datetime
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
KEY = os.getenv('SERPAPI_KEY')
MAX_MONTHLY_USAGE = 190  # ate 190 das 250 buscas: margem de 60
MAX_PRODUCTS = 11       # 11 x 16 execucoes em meses de 31 dias = 176
MIN_CREDITS_REMAINING = 60


def get_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'RadarPrecosPessoal/2.0'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


def account():
    # Account API nao desconta buscas, documentacao oficial da SerpApi.
    return get_json('https://serpapi.com/account.json?' + urllib.parse.urlencode({'api_key': KEY}))


def can_search(a):
    # Siga o plano real da conta; nao autoriza consultas em plano pago.
    if str(a.get('plan_monthly_price', 0)) not in ('0', '0.0', 'None'):
        raise SystemExit('Conta fora do plano gratuito. Atualizacoes interrompidas por seguranca.')
    if int(a.get('searches_per_month', 0)) < 250:
        raise SystemExit('Cota nao corresponde ao plano gratuito esperado. Interrompido.')
    return (int(a.get('this_month_usage', 999999)) < MAX_MONTHLY_USAGE
            and int(a.get('plan_searches_left', 0)) > MIN_CREDITS_REMAINING
            and int(a.get('total_searches_left', 0)) > MIN_CREDITS_REMAINING)


def main():
    if not KEY:
        raise SystemExit('SERPAPI_KEY ausente. Configure como GitHub Actions Secret.')
    products = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
    if len(products) > MAX_PRODUCTS:
        raise SystemExit(f'Maximo de {MAX_PRODUCTS} produtos automáticos no plano conservador; encontrados {len(products)}.')
    path = ROOT / 'data/prices.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data.setdefault('prices', [])
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    seen = {(str(x.get('productId')),str(x.get('date')),str(x.get('store')),str(x.get('price')))
            for x in data['prices']}
    usage = account()  # Se a verificacao falhar, nenhuma busca e feita
    if not can_search(usage):
        print('Limite gratuito protegido. Nenhuma busca realizada. Saldo:', usage.get('plan_searches_left'))
        return
    for p in products:
        usage = account()  # confere saldo antes de cada busca
        if not can_search(usage):
            print('Parada preventiva: limite de uso/saldo SerpApi alcancado.')
            break
        params = urllib.parse.urlencode({
            'engine': 'google_shopping', 'q': p['query'], 'gl': 'br', 'hl': 'pt', 'api_key': KEY
        })
        try:
            result = get_json('https://serpapi.com/search.json?' + params)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 402, 403, 429):
                print('API recusou requisicao (codigo %s). Interrompido.' % exc.code)
                break
            print('Falha para', p['name'], exc)
            continue
        except Exception as exc:
            print('Falha para', p['name'], exc)
            continue
        if result.get('error'):
            print('Resposta com erro; interrompendo:', result['error'])
            break
        # Exige codigo exato do produto, para evitar misturar outros monitores.
        model = p.get('model', '').lower().strip()
        for item in result.get('shopping_results', [])[:20]:
            title = (item.get('title') or '').lower()
            if model and model not in title:
                continue
            price = item.get('extracted_price')
            if not isinstance(price, (float, int)) or isinstance(price, bool) or price <= 0:
                continue
            store = item.get('source') or 'Loja não identificada'
            date = now[:10]
            fingerprint = (str(p['id']), date, store, str(price))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            data['prices'].append({
                'productId': p['id'], 'date': date, 'price': price,
                'shipping': 0, 'shippingKnown': False, 'store': store,
                'condition': 'Novo', 'kind': 'Coleta automática',
                'url': item.get('product_link') or item.get('link') or '',
                'id': 'auto-' + p['id'] + '-' + str(len(data['prices'])),
                'title': item.get('title', ''), 'collectedAt': now
            })
        time.sleep(1)
    data['updated_at'] = now
    data['quota_policy'] = {'max_monthly_usage': MAX_MONTHLY_USAGE, 'monthly_free_plan': 250,
                            'reserved_searches': MIN_CREDITS_REMAINING}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Total de registros:', len(data['prices']))


if __name__ == '__main__':
    main()
