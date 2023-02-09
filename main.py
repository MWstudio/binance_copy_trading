import requests, time
import telegram
from binance.client import Client
from datetime import datetime

chat_id = -671910119
bot = telegram.Bot(token='2075531825:AAFKBzPYwey4-TF6dIoimSS3hVH6tYzM1PA')
set_leverage = 5
position_url = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'
#4C6AAFDF7B5D9C8B1EA324F1D68FFE31
user_payload = {
    'encryptedUid':'391C2981F65164BECCB630D3462C5813',
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

def get_precision(symbol):
    infos = client.futures_exchange_info()['symbols']
    for info in infos:
        if info['symbol'] == symbol:
            precision = info['quantityPrecision']
            break
    return precision

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
    client.futures_change_leverage(symbol = symbol, leverage=set_leverage)
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
            print('position close:', symbol, now.strftime('%Y-%m-%d %H:%M:%S'))
            bot.sendMessage(chat_id=chat_id, text=symbol + "포지션 정리 - " + now.strftime('%Y-%m-%d %H:%M:%S'))

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
    if position == 'BUY':
        pos = 'LONG'
    else:
        pos = 'SHORT'
    bot.sendMessage(chat_id=chat_id, text=symbol + ' ' + pos + " 진입 - " + now.strftime('%Y-%m-%d %H:%M'))
    print('position open:', symbol, now.strftime('%Y-%m-%d %H:%M:%S'))

my_positions = []

while True:
    time.sleep(3)
    ranker_positions = []
    ranker_position_symbol = []
    try:
        res = requests.post(url = position_url, json = user_payload)
        res = res.json()
        ranker_positions = res['data']['otherPositionRetList']
        for ranker_position in ranker_positions:
            my_position = {}
            symbol = ranker_position['symbol']
            amount = ranker_position['amount']
            roe = float("{:.2f}".format(ranker_position['roe']))*100 #진입 가격 비교
            ranker_position_symbol.append(symbol)

            if amount > 0:
                position = 'BUY'
            elif amount < 0:
                position = 'SELL'
            if not is_in_position(symbol): #포지션 진입하지 않은 symbol일때
                if abs(roe) <= 2: 
                    client = Client(API_Key, Secret_Key)
                    my_balance = float(get_my_balance()) / 4
                    now_price = client.futures_symbol_ticker(symbol = symbol)
                    precision = get_precision(symbol)
                    now_price = float(now_price['price'])
                    order_quantity = my_balance * set_leverage / now_price
                    order_quantity = float("{:.{}f}".format(order_quantity, precision))

                    create_order(symbol, position, order_quantity)

                    my_position['symbol'] = symbol
                    my_position['position'] = position
                    my_position['quantity'] = order_quantity
                    my_positions.append(my_position)

        remove_position = []

        for position in my_positions:
            if position['symbol'] not in ranker_position_symbol:
                if is_in_position(position['symbol']):
                    close_order(position['symbol'], position['position'], position['quantity'])
                remove_position.append(position)
        
        for position in remove_position:
            try:
                my_positions.remove(position)
            except Exception as e:
                print(e)
        
    except Exception as e:
        print(e)