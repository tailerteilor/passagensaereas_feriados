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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparador de Destinos: Voos a partir de {origem_local} - LetsFG</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --dest-tag: #8b5cf6;
            --divider: rgba(255, 255, 255, 0.05);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 900px;
            width: 100%;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 50px;
        }

        h1 {
            font-weight: 700;
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }

        .flight-card {
            background-color: var(--card-bg);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
            border: 1px solid var(--divider);
            gap: 20px;
            position: relative;
            overflow: hidden;
        }

        .flight-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
            border-color: rgba(59, 130, 246, 0.3);
        }
        
        .dest-badge {
            position: absolute;
            top: 0;
            left: 0;
            background-color: var(--dest-tag);
            color: white;
            padding: 4px 16px;
            font-size: 0.8rem;
            font-weight: 700;
            border-bottom-right-radius: 12px;
            letter-spacing: 1px;
            z-index: 10;
        }

        .card-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }

        .legs {
            display: flex;
            flex-direction: column;
            gap: 20px;
            flex: 1;
        }

        .leg {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .leg-header {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 700;
        }

        .airlines {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .route {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .time {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .airport {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .flight-path {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            padding: 0 20px;
        }

        .duration {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .line-container {
            width: 100%;
            display: flex;
            align-items: center;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent);
        }

        .line {
            flex: 1;
            height: 2px;
            background: linear-gradient(90deg, var(--accent) 0%, rgba(59, 130, 246, 0.2) 50%, var(--accent) 100%);
        }

        .stops {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .price-action {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 12px;
            min-width: 160px;
            border-left: 1px solid var(--divider);
            padding-left: 20px;
            justify-content: center;
        }

        .price-details {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 4px;
        }

        .price-leg {
            font-size: 1.0rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .price {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--success);
            margin-top: 4px;
        }
        
        .price-label {
            font-size: 1.0rem;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: -4px;
        }
        
        .price-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .price-diff {
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 4px;
        }
        .diff-down { color: var(--success); }
        .diff-up { color: #ef4444; }
        .diff-same { color: var(--text-secondary); }

        .btn-book {
            background-color: var(--accent);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            transition: background-color 0.2s ease;
            text-align: center;
            width: 100%;
            box-sizing: border-box;
        }

        .btn-book:hover {
            background-color: var(--accent-hover);
        }
        
        hr.divider {
            border: 0;
            height: 1px;
            background: var(--divider);
            margin: 0;
        }

        @media (max-width: 700px) {
            .card-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 20px;
            }
            .price-action {
                width: 100%;
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
                border-left: none;
                border-top: 1px solid var(--divider);
                padding-left: 0;
                padding-top: 20px;
            }
            .btn-book {
                width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Para onde viajar?</h1>
            <div class="subtitle">Saindo de {origem_local} | Ida: {data_ida} | Volta: {data_volta}</div>
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
    
    airlines = " + ".join(list(dict.fromkeys([s.get('airline_name') or s.get('airline') for s in segments])))
    
    return f"""
        <div class="leg">
            <div class="leg-header">{leg_title}</div>
            <div class="airlines">{airlines}</div>
            <div class="route">
                <div>
                    <div class="time">{departure_time}</div>
                    <div class="airport">{origin}</div>
                </div>
                
                <div class="flight-path">
                    <div class="duration">{duration}</div>
                    <div class="line-container">
                        <div class="dot"></div>
                        <div class="line"></div>
                        <div class="dot"></div>
                    </div>
                    <div class="stops">{stops}</div>
                </div>

                <div>
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
            <div class="dest-badge" style="background-color: {badge_bg}">Opção para {dest_nome} {emoji} - {tipo}</div>
            <div class="card-content">
                <div class="legs">
                    {outbound_html}
                    {divider}
                    {inbound_html}
                </div>
                <div class="price-action">
                    <div class="price-details">
                        <div class="price-leg">Ida: R$ {ida_price:,.2f}</div>
                        <div class="price-leg">Volta: R$ {volta_price:,.2f}</div>
                    </div>
                    <div class="price-label">Total</div>
                    <div class="price">R$ {brl_price:,.2f}</div>
                    <div class="price-sub">Original: {orig_price}</div>
                    {price_diff_html}
                    <a href="{booking_url}" class="btn-book" target="_blank">Ver Oferta</a>
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
    cmd = f"letsfg search {origem_iata} {dest} {data_ida} --return {data_volta} --mode fast --json"
    print(f"Buscando voos para {dest}...")
    
    # Executa o comando e redireciona a saída para um arquivo, pois o shell do windows lida melhor com isso
    with open(output_file, 'w') as f_out:
        result = subprocess.run(cmd, shell=True, stdout=f_out, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Erro ao buscar {dest}: {result.stderr.decode('utf-8', errors='ignore')}")
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

