import requests, time
from binance.client import Client
from datetime import datetime

position_url = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'
#4C6AAFDF7B5D9C8B1EA324F1D68FFE31
user_payload = {
    'encryptedUid':'4C6AAFDF7B5D9C8B1EA324F1D68FFE31',
    'tradeType':'PERPETUAL'
}

file1 = open('key.txt', 'r')
lines = file1.read().splitlines()
API_Key = lines[0]
Secret_Key = lines[1]
file1.close()

client = Client(API_Key, Secret_Key)

def get_my_balance():
    client = Client(API_Key, Secret_Key)
    futures_account_balance = client.futures_account_balance()
    for balance in futures_account_balance:
        if balance['asset'] == 'USDT':
            futures_balance = balance['balance']
            break

    futures_balance = futures_balance.split('.')[0] + '.' + futures_balance.split('.')[1][0:3]
    return futures_balance

def is_in_position(symbol):
    client = Client(API_Key, Secret_Key)
    info = client.futures_position_information(symbol = symbol)
    if float(info[0]['positionAmt']) == 0: #포지션 진입하지 않은 symbol일때
        return False
    else:
        return True

def get_my_position():
    my_position = []
    client = Client(API_Key, Secret_Key)
    position_info = client.futures_position_information()

    for info in position_info:
        if float(info['positionAmt']) != 0:
            my_position.append(info['symbol'])
    print(my_position)
    return my_position


def change_leverage(symbol):
    client = Client(API_Key, Secret_Key)
    client.futures_change_leverage(symbol = symbol, leverage=20)
    try:
        client.futures_change_margin_type(symbol = symbol, marginType="ISOLATED")
    except:
        pass

def close_order(symbol, position, quantity):
    client = Client(API_Key, Secret_Key)
    orders = client.futures_account()['positions']
    for order in orders:
        if float(order['maintMargin']) > 0 and order['symbol'] == symbol:
            if position == 'BUY':
                position = 'SELL'
            else:
                position = 'BUY'
            client.futures_create_order(
                symbol = symbol,
                type = 'MARKET',
                side = position,
                quantity = quantity
            )
            now = datetime.now()
            print('position close:', symbol, now)

def create_order(symbol, position, order_quantity):
    client = Client(API_Key, Secret_Key)
    change_leverage(symbol)

    client.futures_create_order(
        symbol = symbol,
        type = 'MARKET',
        side = position,
        quantity = order_quantity
    )
    now = datetime.now()
    print('position open:', symbol, now)
# try:
#     create_order('BTCUSDT', 'BUY')
# except:
#     print('start position error')
my_positions = []

while True:
    ranker_positions = []
    ranker_position_symbol = []
    my_position = {}
    try:
        try:
            res = requests.post(url = position_url, json = user_payload)
            res = res.json()
            ranker_positions = res['data']['otherPositionRetList']
        except:
            time.sleep(10)

        for ranker_position in ranker_positions:
            symbol = ranker_position['symbol']
            amount = ranker_position['amount']
            roe = float("{:.2f}".format(ranker_position['roe']))*100 #진입 가격 비교
            ranker_position_symbol.append(symbol)

            if amount > 0:
                position = 'BUY'
            elif amount < 0:
                position = 'SELL'
            else:
                print('what position?')

            
            if not is_in_position(symbol): #포지션 진입하지 않은 symbol일때
                if abs(roe) < 1.5: 
                    client = Client(API_Key, Secret_Key)
                    my_balance = float(get_my_balance()) / 4
                    now_price = client.futures_symbol_ticker(symbol = symbol)
                    now_price = float(now_price['price'])
                    order_quantity = round(my_balance * 20 / now_price, 1) 
                    create_order(symbol, position, order_quantity)
                    my_position['symbol'] = symbol
                    my_position['position'] = position
                    my_position['quantity'] = order_quantity
                    my_positions.append(my_position)
        
        for position in my_positions:
            if position['symbol'] not in ranker_position_symbol:
                close_order(symbol, position['position'], position['quantity'])

    except Exception as e:
        print(e)

'''
ranker_position
[
    {'symbol': 'INJUSDT', 
    'entryPrice': 3.968271233726, 
    'markPrice': 4.043, 
    'pnl': 120.53750601, 
    'roe': 0.18483495, 
    'updateTime': [2023, 2, 7, 8, 5, 32, 144000000], 
    'amount': 1613.0, 
    'updateTimeStamp': 1675757132144, 
    'yellow': False, 
    'tradeBefore': False, 
    'leverage': 10
}, 
{'symbol': 'ALICEUSDT', 'entryPrice': 2.1, 'markPr
ice': 2.17034561, 'pnl': 125.61615577, 'roe': 0.48964893, 'updateTime': [2023, 2, 8, 5, 42, 9, 202000000], 'amount': 1785.7, 'updateTimeStamp': 1675834929202, '
yellow': True, 'tradeBefore': False, 'leverage': 20}, {'symbol': 'LDOUSDT', 'entryPrice': 2.584857142857, 'markPrice': 2.5694, 'pnl': -54.09999, 'roe': -0.06015
856, 'updateTime': [2023, 2, 8, 6, 47, 32, 905000000], 'amount': 3500, 'updateTimeStamp': 1675838852905, 'yellow': True, 'tradeBefore': False, 'leverage': 10},
{'symbol': 'SANDUSDT', 'entryPrice': 0.8954999999999, 'markPrice': 0.8866, 'pnl': -133.49985, 'roe': -0.20076675, 'updateTime': [2023, 2, 8, 5, 45, 7, 810000000
], 'amount': 15000, 'updateTimeStamp': 1675835107810, 'yellow': True, 'tradeBefore': False, 'leverage': 20}, {'symbol': 'JASMYUSDT', 'entryPrice': 0.00800658333
33, 'markPrice': 0.0077425, 'pnl': -158.448, 'roe': -0.68215693, 'updateTime': [2023, 2, 8, 8, 15, 50, 486000000], 'amount': 600000, 'updateTimeStamp': 16758441
50486, 'yellow': True, 'tradeBefore': False, 'leverage': 20}]
'''