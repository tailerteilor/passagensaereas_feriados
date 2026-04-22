import json
from datetime import datetime

USD_TO_BRL = 4.980259
EUR_TO_BRL = USD_TO_BRL / 0.848957

try:
    with open('results_round.json', 'r', encoding='utf-16') as f:
        content = f.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        data = json.loads(content)
except Exception:
    with open('results_round.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voos Ida e Volta: POA ✈ CWB - LetsFG</title>
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
            max-width: 800px;
            width: 100%;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        h1 {
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
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
        }

        .flight-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
            border-color: rgba(59, 130, 246, 0.3);
        }
        
        .card-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
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
            color: var(--accent);
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

        .price {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--success);
        }
        
        .price-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

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
            <h1>Porto Alegre ✈ Curitiba</h1>
            <div class="subtitle">Ida: 30/04/2026 | Volta: 03/05/2026</div>
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

flights_html = ""
offers = data.get('offers', [])

# Sort offers by BRL price
def get_brl_price(offer):
    price = offer.get('price', 0)
    currency = offer.get('currency', '')
    if currency == 'EUR':
        return price * EUR_TO_BRL
    elif currency == 'USD':
        return price * USD_TO_BRL
    return price

offers.sort(key=get_brl_price)

for offer in offers:
    outbound = offer.get('outbound', {})
    inbound = offer.get('inbound', {})
    
    if not outbound.get('segments'):
        continue
        
    brl_price = get_brl_price(offer)
    orig_price = f"{offer.get('price')} {offer.get('currency')}"
    booking_url = offer.get('booking_url', '#')
    
    outbound_html = render_leg("IDA - 30/04/2026", outbound)
    inbound_html = render_leg("VOLTA - 03/05/2026", inbound)
    
    divider = '<hr class="divider">' if inbound_html else ''
    
    flights_html += f"""
        <div class="flight-card">
            <div class="card-content">
                <div class="legs">
                    {outbound_html}
                    {divider}
                    {inbound_html}
                </div>
                <div class="price-action">
                    <div class="price">R$ {brl_price:,.2f}</div>
                    <div class="price-sub">Original: {orig_price}</div>
                    <a href="{booking_url}" class="btn-book" target="_blank">Ver Oferta</a>
                </div>
            </div>
        </div>
    """

final_html = html_template.replace("{flights_html}", flights_html)

with open('index_ida_volta.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("HTML round trip generated successfully.")
