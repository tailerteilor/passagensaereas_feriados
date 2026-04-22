import json

# Exchange rates
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

if not data.get('offers'):
    print("Nenhuma oferta encontrada.")
    exit(0)

cheapest = None
min_brl_price = float('inf')

for offer in data['offers']:
    price = offer['price']
    currency = offer['currency']
    
    brl_price = 0
    if currency == 'EUR':
        brl_price = price * EUR_TO_BRL
    elif currency == 'USD':
        brl_price = price * USD_TO_BRL
    elif currency == 'BRL':
        brl_price = price
    else:
        continue # Ignora outras moedas
        
    if brl_price < min_brl_price:
        min_brl_price = brl_price
        cheapest = offer

if cheapest:
    outbound = cheapest['outbound']['segments'][0]
    inbound = cheapest['inbound']['segments'][0] if cheapest.get('inbound') else None
    
    print(f"Menor preço encontrado: R$ {min_brl_price:.2f}")
    print(f"Moeda Original: {cheapest['price']} {cheapest['currency']}")
    print(f"Id: {cheapest['id']}")
    print(f"Companhia de Ida: {outbound.get('airline_name') or outbound.get('airline')}")
    if inbound:
        print(f"Companhia de Volta: {inbound.get('airline_name') or inbound.get('airline')}")
else:
    print("Nenhuma oferta válida encontrada para conversão.")
