import json
import subprocess
import os
import urllib.request
from datetime import datetime
import concurrent.futures
import threading

# 1. Carregar configuração
with open('config_busca.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

origem_iata = config['origem']
destinos_config = config['destinos']
dest_info = {d['iata']: d for d in destinos_config}
origem_local = dest_info.get(origem_iata, {}).get('local', origem_iata)
destinos = [d['iata'] for d in destinos_config if d.get('buscar') == 'ON']
data_ida = config['data_ida']
data_volta = config['data_volta']
threads_config = config.get('threads', 1)

# 2. Buscar cotação atualizada (USD, EUR, GBP e KWD para BRL)
try:
    req = urllib.request.urlopen("https://open.er-api.com/v6/latest/USD")
    rates_data = json.loads(req.read())
    USD_TO_BRL = rates_data['rates']['BRL']
    EUR_TO_USD = 1 / rates_data['rates']['EUR']
    EUR_TO_BRL = EUR_TO_USD * USD_TO_BRL
    GBP_TO_USD = 1 / rates_data['rates']['GBP']
    GBP_TO_BRL = GBP_TO_USD * USD_TO_BRL
    KWD_TO_USD = 1 / rates_data['rates']['KWD']
    KWD_TO_BRL = KWD_TO_USD * USD_TO_BRL
except Exception as e:
    print("Aviso: Falha ao buscar cotação. Usando valores fallback.")
    USD_TO_BRL = 4.98
    EUR_TO_BRL = 5.86
    GBP_TO_BRL = 6.20
    KWD_TO_BRL = 16.20

def get_brl_price(offer):
    price = offer.get('price', 0)
    currency = offer.get('currency', '')
    if currency == 'EUR':
        return price * EUR_TO_BRL
    elif currency == 'USD':
        return price * USD_TO_BRL
    elif currency == 'GBP':
        return price * GBP_TO_BRL
    elif currency == 'KWD':
        return price * KWD_TO_BRL
    elif currency == 'BRL':
        return price
    return price


# 3. Carregar Histórico de Preços
HISTORICO_FILE = 'historico_precos.json'
historico = {}
if os.path.exists(HISTORICO_FILE):
    try:
        with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
            historico = json.load(f)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar o histórico ({e})")

# 4. HTML Template e Funções
# 5. Gerar HTML Bonitão
html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Comparador de Destinos: Voos a partir de {origem_local} - LetsFG</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f8fafc;
            --surface: #ffffff;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --success: #059669;
            --danger: #dc2626;
            --divider: #f1f5f9;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
            --radius: 16px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            padding: 20px 16px 60px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 32px;
            padding: 20px 0;
        }

        h1 {
            font-weight: 800;
            font-size: clamp(1.75rem, 5vw, 2.5rem);
            color: var(--text-primary);
            margin-bottom: 12px;
            letter-spacing: -0.025em;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: clamp(0.875rem, 3vw, 1.05rem);
            font-weight: 500;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px 16px;
        }
        
        .subtitle-item {
            display: inline-flex;
            align-items: center;
        }

        #flights-container {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .flight-card {
            background: var(--surface);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .flight-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
            border-color: #cbd5e1;
        }

        .dest-badge {
            padding: 10px 16px;
            font-size: 0.9rem;
            font-weight: 700;
            color: white;
            text-align: center;
            letter-spacing: 0.5px;
        }

        .card-content {
            padding: 24px;
        }

        .legs {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .leg {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .leg-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .leg-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-secondary);
            font-weight: 700;
            background: var(--bg);
            padding: 4px 10px;
            border-radius: 6px;
        }

        .airlines {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .route {
            display: grid;
            grid-template-columns: minmax(60px, auto) 1fr minmax(60px, auto);
            align-items: center;
            gap: 16px;
        }

        .route-point {
            text-align: center;
        }
        
        .route-point.left { text-align: left; }
        .route-point.right { text-align: right; }

        .time {
            font-size: clamp(1.25rem, 4vw, 1.5rem);
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.2;
        }

        .airport {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-top: 4px;
        }

        .flight-path {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
        }

        .duration {
            font-size: 0.8rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 6px;
        }

        .line-wrapper {
            width: 100%;
            display: flex;
            align-items: center;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #cbd5e1;
            border: 2px solid var(--surface);
            box-shadow: 0 0 0 1px #cbd5e1;
            z-index: 1;
        }

        .line {
            flex: 1;
            height: 2px;
            background-color: #cbd5e1;
            margin: 0 -2px;
        }

        .stops {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-top: 6px;
        }

        .stops.direct {
            color: var(--success);
            font-weight: 600;
        }

        .divider {
            height: 1px;
            background-color: var(--divider);
            margin: 0;
            border: none;
        }

        .price-action {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: end;
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid var(--divider);
            gap: 16px;
        }

        .price-col {
            display: flex;
            flex-direction: column;
        }
        
        .price-col.left { align-items: flex-start; }
        .price-col.center { align-items: center; }
        .price-col.right { align-items: flex-end; text-align: right; }

        .price-leg {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 4px;
        }

        .price-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 700;
            margin-bottom: 6px;
        }

        .price {
            font-size: clamp(1.75rem, 5vw, 2.25rem);
            font-weight: 800;
            color: var(--success);
            line-height: 1;
        }

        .price-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .price-diff {
            font-size: 0.85rem;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 12px;
        }
        
        .diff-down { background: #dcfce7; color: #166534; }
        .diff-up   { background: #fee2e2; color: #991b1b; }
        .diff-same { background: #f1f5f9; color: #475569; }

        .btn-book {
            background-color: var(--accent);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            text-align: center;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
        }

        .btn-book:hover {
            background-color: var(--accent-hover);
            transform: translateY(-1px);
        }

        /* Responsividade */
        @media (max-width: 640px) {
            .card-content {
                padding: 16px;
            }
            
            .route {
                gap: 10px;
            }

            .price-action {
                grid-template-columns: 1fr;
                gap: 20px;
                text-align: center;
                align-items: center;
            }

            .price-col.left, .price-col.center, .price-col.right {
                align-items: center;
                text-align: center;
            }
            
            .price-col.left {
                flex-direction: row;
                justify-content: center;
                gap: 16px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--divider);
                width: 100%;
            }
            
            .price-leg {
                margin-bottom: 0;
            }

            .price-diff {
                margin-bottom: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>✈️ Para onde viajar?</h1>
            <div class="subtitle">
                <span class="subtitle-item">Saindo de <strong>&nbsp;{origem_local}</strong></span>
                <span class="subtitle-item" style="color:var(--border)">|</span>
                <span class="subtitle-item">Ida: <strong>&nbsp;{data_ida}</strong></span>
                <span class="subtitle-item" style="color:var(--border)">|</span>
                <span class="subtitle-item">Volta: <strong>&nbsp;{data_volta}</strong></span>
            </div>
        </header>
        <div id="flights-container">
            {flights_html}
        </div>
    </div>
</body>
</html>
"""

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def format_time(date_str):
    if not date_str:
        return ""
    dt_str = date_str.split("-03:00")[0]
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%H:%M")

def render_leg(leg_title, leg_data):
    if not leg_data: return ""
    segments = leg_data.get('segments', [])
    if not segments: return ""
    
    first_segment = segments[0]
    last_segment = segments[-1]
    
    departure_time = format_time(first_segment.get('departure'))
    arrival_time = format_time(last_segment.get('arrival'))
    
    origin = first_segment.get('origin', '')
    destination = last_segment.get('destination', '')
    
    duration = format_duration(leg_data.get('total_duration_seconds', 0))
    stopovers = leg_data.get('stopovers', 0)
    stops = "Voo Direto" if stopovers == 0 else f"{stopovers} Parada{'s' if stopovers > 1 else ''}"
    stops_class = "direct" if stopovers == 0 else ""
    
    airlines = " + ".join(list(dict.fromkeys([s.get('airline_name') or s.get('airline') for s in segments])))
    
    return f"""
        <div class="leg">
            <div class="leg-header-row">
                <div class="leg-title">{leg_title}</div>
                <div class="airlines">{airlines}</div>
            </div>
            <div class="route">
                <div class="route-point left">
                    <div class="time">{departure_time}</div>
                    <div class="airport">{origin}</div>
                </div>

                <div class="flight-path">
                    <div class="duration">{duration}</div>
                    <div class="line-wrapper">
                        <div class="dot"></div>
                        <div class="line"></div>
                        <div class="dot"></div>
                    </div>
                    <div class="stops {stops_class}">{stops}</div>
                </div>

                <div class="route-point right">
                    <div class="time">{arrival_time}</div>
                    <div class="airport">{destination}</div>
                </div>
            </div>
        </div>
    """


def save_html(offers_list, filename):
    offers_sorted = sorted(offers_list, key=get_brl_price)

    # Filtrar apenas a opção mais barata por destino
    cheapest_offers = []
    seen_dests = set()
    for offer in offers_sorted:
        dest_code = offer.get('_search_dest')
        if dest_code and dest_code not in seen_dests:
            cheapest_offers.append(offer)
            seen_dests.add(dest_code)

    flights_html = ""
    for offer in cheapest_offers:
        outbound = offer.get('outbound', {})
        inbound = offer.get('inbound', {})
        
        if not outbound.get('segments'):
            continue
            
        dest_code = offer['_search_dest']
        info = dest_info.get(dest_code, {})
        dest_nome = info.get('local', dest_code)
        emoji = info.get('emoji', '📍')
        tipo = info.get('tipo', 'destino').replace('_', ' ').title()
        
        brl_price = get_brl_price(offer)
        ida_price = brl_price / 2
        volta_price = brl_price / 2
        orig_price = f"{offer.get('price')} {offer.get('currency')}"
        booking_url = offer.get('booking_url', '#')
        
        price_diff_html = ""
        old_price = historico.get(dest_code)
        if old_price is not None and old_price > 0:
            diff_pct = ((brl_price - old_price) / old_price) * 100
            if diff_pct < 0:
                price_diff_html = f'<div class="price-diff diff-down">↓ {abs(diff_pct):.1f}% vs última busca</div>'
            elif diff_pct > 0:
                price_diff_html = f'<div class="price-diff diff-up">↑ {diff_pct:.1f}% vs última busca</div>'
            else:
                price_diff_html = f'<div class="price-diff diff-same">= Preço estável</div>'
        
        outbound_html = render_leg(f"IDA", outbound)
        inbound_html = render_leg(f"VOLTA", inbound)
        
        divider = '<hr class="divider">' if inbound_html else ''
        
        hash_num = sum([ord(c) for c in dest_code])
        hue = (hash_num * 137.5) % 360
        badge_bg = f"hsl({hue}, 70%, 50%)"
        
        flights_html += f'''
        <div class="flight-card" data-dest="{dest_code}">
            <div class="dest-badge" style="background-color: {badge_bg}">{emoji} {dest_nome} &mdash; {tipo}</div>
            <div class="card-content">
                <div class="legs">
                    {outbound_html}
                    {divider}
                    {inbound_html}
                </div>
                <div class="price-action">
                    <div class="price-col left">
                        <div class="price-leg">Ida: R$ {ida_price:,.2f}</div>
                        <div class="price-leg">Volta: R$ {volta_price:,.2f}</div>
                    </div>
                    <div class="price-col center">
                        <div class="price-label">Preço Total</div>
                        <div class="price">R$ {brl_price:,.2f}</div>
                    </div>
                    <div class="price-col right">
                        <div class="price-sub">Original: {orig_price}</div>
                        {price_diff_html}
                        <a href="{booking_url}" class="btn-book" target="_blank">
                            Ver Oferta
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        '''

    final_html = html_template.replace("{origem_local}", origem_local)\
                              .replace("{data_ida}", data_ida)\
                              .replace("{data_volta}", data_volta)\
                              .replace("{flights_html}", flights_html)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_html)


# 3. Rodar buscas para cada destino e coletar resultados
all_offers = []

if not os.path.exists('temp'):
    os.makedirs('temp')

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print(f"Iniciando busca de passagens de {origem_local} para {', '.join(destinos)}...")
print(f"Ida: {data_ida} | Volta: {data_volta}\n")

write_lock = threading.Lock()

def search_destination(dest):
    output_file = f"temp/result_{dest}_{timestamp}.json"
    cmd = f"python -m letsfg search {origem_iata} {dest} {data_ida} --return {data_volta} --mode fast --json"
    print(f"Buscando voos para {dest}...")
    
    # Executa o comando e redireciona a saída para um arquivo, pois o shell do windows lida melhor com isso
    with open(output_file, 'w') as f_out:
        result = subprocess.run(cmd, shell=True, stdout=f_out, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        err_msg = result.stderr.decode('utf-8', errors='ignore')
        out_msg = ""
        try:
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f_out_read:
                out_msg = f_out_read.read()
        except Exception:
            pass
        print(f"Erro ao buscar {dest}: returncode={result.returncode} | stderr={err_msg} | stdout={out_msg}")
        return
        
    # Ler o JSON gerado
    try:
        # Tenta ler com utf-16 primeiro (padrão de redirecionamento de algumas versões do PS)
        try:
            with open(output_file, 'r', encoding='utf-16') as f_json:
                content = f_json.read()
                if content.startswith('\ufeff'):
                    content = content[1:]
                data = json.loads(content)
        except Exception:
            with open(output_file, 'r', encoding='utf-8-sig') as f_json:
                data = json.load(f_json)
                
        if 'offers' in data:
            # Tag the destination in the offer so we know where it goes
            for offer in data['offers']:
                offer['_search_dest'] = dest
                
            with write_lock:
                all_offers.extend(data['offers'])
                print(f"-> {len(data['offers'])} opções encontradas para {dest}.")
                print(f"-> Atualizando index_multidestino.html.temp com dados de {dest}...")
                save_html(all_offers, 'index_multidestino.html.temp')
    except Exception as e:
        print(f"Erro ao processar resultados de {dest}: {e}")

if threads_config > 1:
    print(f"-> Execução PARALELA ativada com {threads_config} threads.\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads_config) as executor:
        executor.map(search_destination, destinos)
else:
    print("-> Execução SEQUENCIAL ativada.\n")
    for dest in destinos:
        search_destination(dest)


# 5. Gerar versão final
save_html(all_offers, 'index_multidestino.html')

print("\nProcesso finalizado!")
print("HTML gerado: index_multidestino.html")
if os.path.exists('index_multidestino.html.temp'):
    try:
        os.remove('index_multidestino.html.temp')
    except Exception:
        pass

# 6. Atualizar Histórico de Preços
cheapest_current = {}
for offer in all_offers:
    dest_code = offer.get('_search_dest')
    if not dest_code: continue
    price = get_brl_price(offer)
    if dest_code not in cheapest_current or price < cheapest_current[dest_code]:
        cheapest_current[dest_code] = price

for dest, price in cheapest_current.items():
    historico[dest] = price

try:
    with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4)
    print("Histórico de preços atualizado com sucesso!")
except Exception as e:
    print(f"Erro ao salvar histórico: {e}")

