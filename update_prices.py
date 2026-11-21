"""Coleta conservadora: plano gratuito confirmado antes de cada busca."""
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
MAX_MONTHLY_USAGE, RESERVE, MAX_PRODUCTS = 190, 60, 11

class SafeStop(Exception):
    pass

def get_json(endpoint, params):
    # Nunca registrar URLs, respostas da conta ou exceções com credenciais.
    url = 'https://serpapi.com/' + endpoint + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'RadarPrecos/3'})
        with urllib.request.urlopen(req, timeout=45) as response:
            value = json.load(response)
    except Exception:
        raise SafeStop('Falha ao consultar SerpApi; coleta interrompida.') from None
    if not isinstance(value, dict) or value.get('error'):
        raise SafeStop('Resposta inválida ou erro da SerpApi; coleta interrompida.')
    return value

def quota(a):
    # Todos os campos devem estar presentes, tipados e coerentes.
    if (a.get('account_status') != 'Active'
        or a.get('plan_id') not in ('free', 'free_plan')
        or a.get('plan_name') not in ('Free', 'Free Plan')
        or type(a.get('plan_monthly_price')) not in (int, float)
        or a['plan_monthly_price'] != 0
        or type(a.get('searches_per_month')) is not int
        or a['searches_per_month'] != 250):
        raise SafeStop('Não foi possível confirmar plano gratuito ativo de 250 buscas.')
    fields = ('this_month_usage', 'plan_searches_left', 'total_searches_left')
    if any(type(a.get(k)) is not int or a[k] < 0 for k in fields):
        raise SafeStop('Saldo ausente ou inválido; nenhuma nova busca autorizada.')
    try:
        renewal = dt.date.fromisoformat(a['plan_renewal_date'])
    except (KeyError, ValueError, TypeError):
        raise SafeStop('Ciclo da franquia não confirmado.') from None
    if a['this_month_usage'] + a['plan_searches_left'] != 250:
        raise SafeStop('Saldo inconsistente; coleta interrompida.')
    return {'used': a['this_month_usage'], 'remaining': a['plan_searches_left'],
            'renewal': renewal.isoformat(), 'safe_remaining': max(0, min(
                190-a['this_month_usage'], a['plan_searches_left']-60,
                a['total_searches_left']-60))}

def normalize(s):
    return re.sub(r'[^A-Z0-9]', '', str(s).upper())

def matches(p, title):
    # Fronteiras impedem Q27G4F/CQ27G4F e 24G4/24G4E.
    title = str(title).upper()
    codes = p.get('match_models', [p['model']])
    for code in codes:
        parts = re.findall(r'[A-Z0-9]+', code.upper())
        pattern = r'(?<![A-Z0-9])' + r'[\s\-/]*'.join(map(re.escape, parts)) + r'(?![A-Z0-9])'
        if re.search(pattern, title):
            if p.get('size_required') and not re.search(r'\b24(?:[.,]0)?\s*(?:["″]|POLEGADAS|POL\b)', title):
                continue
            return True
    return False

def review_reason(p, title, store):
    reasons = []
    hz = re.findall(r"(\d+)\s*HZ", title.upper())
    if p.get('refresh_hz') and hz and str(p['refresh_hz']) not in hz:
        reasons.append('Frequência do anúncio diverge da ficha oficial')
    if not re.search(r'kabum|pichau|terabyte|amazon|mercado livre|magazine luiza|magalu|casas bahia|lg electronics|samsung|shopee|fast shop', store, re.I):
        reasons.append('Loja fora das fontes prioritárias; confirmar origem e condições')
    return '; '.join(reasons)

def due(p, data, now):
    previous = data.get('product_checks', {}).get(p['id'])
    if not previous:
        return True
    last = dt.datetime.fromisoformat(previous)
    special = now.astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat() in ('2026-11-26','2026-11-27','2026-11-30')
    if special:
        return last.astimezone(ZoneInfo('America/Sao_Paulo')).date() != now.astimezone(ZoneInfo('America/Sao_Paulo')).date()
    return (now-last).total_seconds() >= 48*3600

def write_data(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False, encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    os.replace(f.name, path)

def collect(data, products, key, now):
    data.setdefault('prices', [])
    data.setdefault('product_checks', {})
    data['quota_policy'] = {'max_monthly_usage':190,'monthly_free_plan':250,'reserved_searches':60,'max_products':11}
    if len(products)>11 or len({p['id'] for p in products}) != len(products):
        raise SafeStop('Catálogo inválido: limite de 11 produtos ou IDs repetidos.')
    attempts = 0
    baseline = None
    for p in products:
        if not due(p, data, now):
            continue
        q = quota(get_json('account.json', {'api_key':key}))
        if baseline is None:
            baseline = q.copy()
        if q['renewal'] != baseline['renewal']:
            raise SafeStop('Ciclo mudou durante execução; tente novamente depois.')
        # Contador local protege mesmo se a Account API demorar para atualizar.
        available = min(q['safe_remaining'], baseline['safe_remaining']-attempts)
        data['api_usage'] = {**q, 'safe_remaining':max(0,available),'checked_at':now.isoformat(),'verified':True}
        if available <= 0:
            data['collection_status'] = 'Reserva de segurança atingida.'
            break
        attempts += 1
        result = get_json('search.json', {'engine':'google_shopping','q':p['query'],'gl':'br','hl':'pt','api_key':key})
        if result.get('search_metadata', {}).get('status') != 'Success':
            raise SafeStop('Busca não confirmou sucesso; execução interrompida.')
        items = result.get('shopping_results', [])
        if not isinstance(items, list):
            raise SafeStop('Lista de ofertas inválida.')
        for item in items:
            if not isinstance(item, dict) or not matches(p, item.get('title','')):
                continue
            price = item.get('extracted_price')
            if type(price) not in (int,float) or not math.isfinite(price) or price<=0:
                continue
            title = item.get('title','')
            if not re.match(r'^R\$\s*', str(item.get('price',''))):
                continue  # Não interpretar moeda estrangeira como reais.
            # Não misturar usados, recondicionados ou kits com preços de novos.
            if re.search(r'\b(usado|seminovo|recondicionado|refurbished|kit)\b', title, re.I):
                continue
            url = item.get('link') or item.get('product_link') or ''
            if urllib.parse.urlsplit(url).scheme not in ('http','https'):
                url = ''
            record = {'productId':p['id'],'date':now.astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat(),
                'price':price,'shipping':None,'shippingKnown':False,'store':item.get('source') or 'Loja não identificada',
                'condition':'Novo','kind':'Coleta automática','url':url,'title':title,
                'collectedAt':now.isoformat(),'source':'SerpApi Google Shopping','cartConfirmed':False}
            record['reviewReason'] = review_reason(p, title, record['store'])
            record['currency'] = 'BRL'
            thumbnail = item.get('thumbnail')
            if isinstance(thumbnail, str) and urllib.parse.urlsplit(thumbnail).scheme == 'https':
                record['image'] = thumbnail
            fingerprint = '|'.join(str(record[k]) for k in ('productId','date','price','store','url'))
            record['id'] = 'auto-' + hashlib.sha256(fingerprint.encode()).hexdigest()[:24]
            if not any(r.get('id') == record['id'] for r in data['prices']):
                data['prices'].append(record)
        data['product_checks'][p['id']] = now.isoformat()
        data['updated_at'] = now.isoformat()
        data['collection_status'] = 'Coleta concluída; preços anunciados, frete não confirmado.'
    if attempts:
        final = quota(get_json('account.json', {'api_key':key}))
        final['used'] = max(final['used'], baseline['used']+attempts)
        final['remaining'] = min(final['remaining'], baseline['remaining']-attempts)
        final['safe_remaining'] = max(0,min(final['safe_remaining'],baseline['safe_remaining']-attempts))
        data['api_usage'] = {**final,'checked_at':now.isoformat(),'verified':True,'conservative':True}
    return attempts

def main():
    path = ROOT/'data/prices.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    # Mantém histórico legado sem duplicar.
    if (ROOT/'prices.json').exists():
        old = json.loads((ROOT/'prices.json').read_text(encoding='utf-8'))
        for row in old.get('prices',[]):
            if row not in data.setdefault('prices',[]):
                data['prices'].append(row)
    try:
        key = os.environ.get('SERPAPI_KEY')
        if not key:
            raise SafeStop('SERPAPI_KEY ausente nos Secrets do GitHub Actions.')
        products = json.loads((ROOT/'products.json').read_text(encoding='utf-8'))
        count = collect(data, products, key, dt.datetime.now(dt.timezone.utc))
        print(f'Execução concluída: {count} buscas; {len(data["prices"])} registros preservados.')
    except SafeStop as exc:
        data['collection_status'] = str(exc)
        data['api_usage'] = {**data.get('api_usage',{}),'verified':False}
        print(str(exc))
        write_data(data,path)
        return 1
    write_data(data,path)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
