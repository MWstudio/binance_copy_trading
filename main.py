from binance.client import Client

client = Client('1', '1')
print('login')

info = client.get_account()

bal = info['balances']
for b in bal:
    if b['free'] != '0.00000000':
        print(b)
