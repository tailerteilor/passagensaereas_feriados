import json
from datetime import datetime

with open('results_utf8.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voos POA ✈ CWB - LetsFG</title>
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
            margin-bottom: 20px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .flight-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
            border-color: rgba(59, 130, 246, 0.3);
        }

        .flight-info {
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex: 1;
        }

        .airlines {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
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
            min-width: 150px;
        }

        .price {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--success);
        }

        .btn-book {
            background-color: var(--accent);
            color: white;
            text-decoration: none;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 600;
            transition: background-color 0.2s ease;
        }

        .btn-book:hover {
            background-color: var(--accent-hover);
        }

        @media (max-width: 600px) {
            .flight-card {
                flex-direction: column;
                align-items: flex-start;
                gap: 20px;
            }
            .price-action {
                width: 100%;
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
                border-top: 1px solid rgba(255,255,255,0.1);
                padding-top: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Porto Alegre ✈ Curitiba</h1>
            <div class="subtitle">Resultados da busca para 30/03/2026 (Exibindo opções disponíveis)*</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 5px;">* Como a data solicitada já passou, foram encontradas as melhores opções mais próximas.</div>
        </header>

        <div id="flights-container">
            {flights_html}
        </div>
    </div>
</body>
</html>
"""

flight_html_template = """
            <div class="flight-card">
                <div class="flight-info">
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
                <div class="price-action">
                    <div class="price">{price}</div>
                    <a href="{booking_url}" class="btn-book" target="_blank">Ver Oferta</a>
                </div>
            </div>
"""

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def format_time(date_str):
    if not date_str:
        return ""
    # "2026-05-30T09:05:00" or "2026-05-30T05:50:00-03:00"
    dt_str = date_str.split("-03:00")[0]
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%H:%M")

flights_html = ""
for offer in data.get('offers', []):
    outbound = offer.get('outbound', {})
    segments = outbound.get('segments', [])
    if not segments:
        continue
    
    first_segment = segments[0]
    last_segment = segments[-1]
    
    departure_time = format_time(first_segment.get('departure'))
    arrival_time = format_time(last_segment.get('arrival'))
    
    origin = first_segment.get('origin', 'POA')
    destination = last_segment.get('destination', 'CWB')
    
    duration = format_duration(outbound.get('total_duration_seconds', 0))
    stopovers = outbound.get('stopovers', 0)
    stops = "Voo Direto" if stopovers == 0 else f"{stopovers} Parada{'s' if stopovers > 1 else ''}"
    
    airlines = " + ".join(list(dict.fromkeys([s.get('airline_name') or s.get('airline') for s in segments])))
    
    price = offer.get('price_formatted', f"US$ {offer.get('price')}")
    booking_url = offer.get('booking_url', '#')
    
    flights_html += flight_html_template.format(
        airlines=airlines,
        departure_time=departure_time,
        arrival_time=arrival_time,
        origin=origin,
        destination=destination,
        duration=duration,
        stops=stops,
        price=price,
        booking_url=booking_url
    )

final_html = html_template.replace("{flights_html}", flights_html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("HTML generated successfully.")
