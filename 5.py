# cd PycharmProjects\bybit_webs\venv\Scripts
# activate.bat      =>  python 5.py
#************************************ ПРОБОЙ УРОВНЯ ***********************************
# Скрипт подключается к вебсокету без pybit. Открывает сделку, выставляет стоп лосс
#

from config import API_KEY, SECRET_KEY, Bot, Chat_id
import websockets
import asyncio
import json
import time, datetime
import requests
from pybit.unified_trading import HTTP

sum = 140  # Сумма с которой работаем.если 200 то с 20м плечём это 10 дол залог
coef_list = {'BTCUSDT': 0.5, 'ETHUSDT': 0.6, '1000PEPEUSDT': 0.3, 'BCHUSDT': 1, 'LTCUSDT': 0.55, 'LINKUSDT': 0.4,
             'MDTUSDT': 1,'AVAXUSDT': 1, 'BNBUSDT': 1, 'XRPUSDT': 1, 'MATICUSDT': 1, 'COMPUSDT': 1, 'APTUSDT': 0.18, 'OPUSDT': 1,
             'FILUSDT': 1, 'SUIUSDT': 0.18, 'ARBUSDT':0.3, 'SOLUSDT': 1, 'WLDUSDT': 1, 'AUCTIONUSDT': 0.2,'ETHWUSDT':0.15}

pair_list = {'BTCUSDT': 0.002, 'ETHUSDT': 0.002, '1000PEPEUSDT': 0.004, 'BCHUSDT': 0.002, 'LTCUSDT': 0.002,
             'LINKUSDT': 0.003, 'MDTUSDT': 0.002,'AVAXUSDT': 0.004, 'BNBUSDT': 0.002, 'XRPUSDT': 0.002, 'MATICUSDT': 0.002,
             'COMPUSDT': 0.004,'APTUSDT': 0.007, 'OPUSDT': 0.008,'FILUSDT': 0.002, 'SUIUSDT': 0.02, 'ARBUSDT':0.006,
             'SOLUSDT': 0.002, 'WLDUSDT': 0.005,'AUCTIONUSDT': 0.008,'ETHWUSDT':0.007}

list_count = {'BTCUSDT': 5, 'ETHUSDT': 6, '1000PEPEUSDT': 5, 'BCHUSDT': 11, 'LTCUSDT': 10, 'LINKUSDT': 10,'MDTUSDT': 11,
              'AVAXUSDT': 11, 'BNBUSDT': 50, 'XRPUSDT': 11, 'MATICUSDT': 10, 'COMPUSDT': 20, 'APTUSDT': 10,'OPUSDT': 11,
              'FILUSDT': 11, 'SUIUSDT': 10, 'ARBUSDT': 10, 'SOLUSDT': 10, 'WLDUSDT': 11, 'AUCTIONUSDT': 2,'ETHWUSDT':1}


async def main(symbol, level):  # wss://stream.bybit.com/realtime - trade.BTCUSD если spot
    print('функция - main')
    global list_count
    max_count = list_count[f'{symbol}']
    url = "wss://stream.bybit.com/v5/public/linear"  # wss://stream.bybit.com/v5/public/linear -если orderbook
    subscription = {
        "op": "subscribe",
        "args": [f"publicTrade.{symbol}"]  # orderbook.1.BTCUSDT  publicTrade.ETHUSDT если perpetual
    }
    while True:
        try:
            async with websockets.connect(url) as client:
                print('Начало скрипта')
                qty, qty_list, min_step = min_lot(symbol)  # РАСЧИТАТЬ ЛОТНОСТЬ ЧАСТИЧНОГО ЗАКРЫТИЯ ЗДЕСЬ
                balance = get_wallet()  # Сделать запрос на кошель сколько денег
                counter = -1
                old_millisec = -1
                await client.send(json.dumps(subscription))
                while True:
                    mass = json.loads(await client.recv())
                    data = mass.get('data')
                    if data != None:
                        for el in data:
                            data_price = float(el['p'])
                            if counter==-1:# Если в первом запросе цена уже выше уровня,то заканчивает выполнение скрипта
                                if direction > 0 and data_price > level:
                                    break
                                if direction < 0 and data_price < level:
                                    break

                            data_unixtime = el['T']
                            now_millis = data_unixtime % 1000

                            if counter > max_count and direction > 0 and data_price > level:  # Если движение вверх- покупка
                                mess = f'new order-{symbol} side-Buy price={data_price} time-{conv_un_time(data_unixtime)} '
                                print(mess)
                                send_message(mess)
                                side = 'Buy'
                                return side, qty, qty_list, min_step, balance
                            if counter > max_count and direction < 0 and data_price < level:  # Если движение вниз- продажа
                                mess = f'new order-{symbol} side-Sell price={data_price} time-{conv_un_time(data_unixtime)}  '
                                print(mess)
                                send_message(mess)
                                side = 'Sell'
                                return side, qty, qty_list, min_step, balance

                            if now_millis < old_millisec:  # Начало новой секунды
                                # print(f'Начало новой секунды {time_now()}')
                                # print(f'{symbol} Торговый скрипт')
                                # print(f'now_millis = {now_millis} counter={counter} '
                                #        f'price={data_price} level+dir {level} + {direction}')
                                counter = 0
                            if now_millis == 0:
                                print(f'{symbol} Торговый скрипт'
                                      f'price={data_price} level+dir {level} + {direction}')
                            old_millisec = now_millis
                            counter += 1
        except Exception as e:
            print(f"Ошибка внутри main: {e}")
            print("Перезапуск скрипта через 15 секунд...")
            time.sleep(15)


def conv_un_time(millis):
    unix_time = millis / 1000
    dt = datetime.datetime.utcfromtimestamp(unix_time)
    gmt3_tz = datetime.timezone(datetime.timedelta(hours=3))
    dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone(gmt3_tz)
    return (dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])


def time_sec():
    loc_sec = time.gmtime().tm_sec
    return loc_sec


def time_now():
    loc_sec = time.gmtime().tm_sec
    loc_hour = time.localtime().tm_hour
    loc_min_plus_one = time.gmtime().tm_min
    loc_min = loc_min_plus_one - 1
    loc_date = time.gmtime().tm_mday
    loc_month = time.gmtime().tm_mon
    loc_year = time.gmtime().tm_year
    return f'{loc_year}-{loc_month}-{loc_date} {loc_hour}-{loc_min}-{loc_sec}'


def send_message(mess):
    bot = Bot
    chat_id = Chat_id
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    params = {'chat_id': chat_id, 'text': mess}
    resp = requests.post(url, data=params)
    print('resp', resp)


def min_lot(symbol):  # Функция вычисляет минимальный лот и лоты поэтапного закрытия ордера
    print('Функция - min_lot')
    global sum
    sum_coef = sum * (coef_list[f'{symbol}'])
    qty_list = []
    session = HTTP(testnet=False)
    inf = (session.get_instruments_info(
        category="linear",
        symbol=symbol))
    min_step = float(inf['result']['list'][0]['priceFilter'][
                         'tickSize'])  # найти минимальный шаг символа и при расчете стоп лосса округлять до него
    min_lot = float(inf['result']['list'][0]['lotSizeFilter']['minOrderQty'])
    lastprice = order_book(symbol)
    lot = sum_coef / lastprice  # расчитываем лот. Сумма на счете/цену актива
    not_form_round_lot = lot - (lot % min_lot)  # таким лотом будет открыта сделка
    round_lot_str = '{:.10f}'.format(not_form_round_lot)
    round_lot = float(round_lot_str)
    half_lot = round_lot / 2.5  # первые два тейка закроются с 1/4 от суммы сделки
    first_sec_part_price = half_lot - (half_lot % min_lot)
    first_sec_part_price_str = '{:.10f}'.format(first_sec_part_price)
    first_sec_part_price = float(first_sec_part_price_str)
    last_part_lot = round_lot - (first_sec_part_price * 2)
    last_part_price = round(last_part_lot, 10)
    print(f'last_part_price {last_part_price}')
    if half_lot < min_lot:  # когда лот очень маленький и невозможно делить закрываем одной частью
        qty_list = [f'{round_lot}', '0.0', '0.0']
        print(f'первая часть {round_lot} вторая и третья часть 0,0')
        print(f'min lot {min_lot} min_step={min_step}  round_lot {round_lot}  lastprice {lastprice}')
        print('qty_list-', qty_list)
        return round_lot, qty_list, min_step
    first_sec_part_price = str(first_sec_part_price)
    qty_list.append(first_sec_part_price)
    qty_list.append(first_sec_part_price)

    last_part_price = str(last_part_price)
    qty_list.append(last_part_price)
    print(f'первая и вторая часть {first_sec_part_price}  последняя часть ордера {last_part_price}')
    print(f'min lot {min_lot} min_step={min_step}  round_lot {round_lot}  lastprice {lastprice}')
    print('qty_list-', qty_list)
    return round_lot, qty_list, min_step


def order_book(symbol):  # Возвращает последний ask, для расчета лота сделки
    session = HTTP(testnet=False)
    ordbook = (session.get_orderbook(
        category="linear",
        symbol=symbol,
        limit=1))
    last = float(ordbook['result']['a'][0][0])
    return last


def stop_loss(symbol, level, side, min_step):
    global pair_list
    coef = pair_list[f'{symbol}']
    print(f'coef {coef}')
    if side == 'Buy':
        stop = level - (level * coef)
        stop = stop - (stop % min_step)
        stop_str = '{:.10f}'.format(stop)
        stop = float(stop_str)
        mess = f'stop-loss={stop}'
        send_message(mess)
        print(mess)
        return stop
    else:
        stop = level + (level * coef)
        stop = stop - (stop % min_step)
        stop_str = '{:.10f}'.format(stop)
        stop = float(stop_str)
        mess = f'stop-loss={stop}'
        send_message(mess)
        print(mess)
        return stop


def new_order(symbol, side, qty, level, min_step):  # Открываем Новый ордер
    print('Функция - new_order')
    stop_price = stop_loss(symbol, level, side, min_step)
    session = HTTP(testnet=False,
                   api_key=API_KEY,
                   api_secret=SECRET_KEY, )
    print(session.place_order(
        category="linear",
        symbol=symbol,  # "XRPUSDT"
        side=side,  # 'Buy' or 'Sell'
        orderType="Market",
        qty=qty,
        stopLoss=stop_price))
    return stop_price


def limit_order(symbol, side, level, qty_list):  # Выставляем лимитники для частичной фиксации прибыли
    print('Функция - limit_order')
    global pair_list
    coef = pair_list[f'{symbol}']
    qty1, qty2, qty3 = qty_list
    if side == 'Sell':
        side_lim = 'Buy'
        price1 = str(level - (level * coef * 2))  # (level - (level*0.004))
        price2 = str(level - (level * coef * 3))  # (level - (level*0.006))
        price3 = str(level - (level * coef * 10))  # (level - (level*0.012))
    else:
        side_lim = 'Sell'
        price1 = str(level + (level * coef * 2))
        price2 = str(level + (level * coef * 3))
        price3 = str(level + (level * coef * 10))  # (level - (level*0.009))
    price_list = []
    price_list.append(price1)
    price_list.append(price2)
    price_list.append(price3)
    session = HTTP(
        testnet=False,
        api_key=API_KEY,
        api_secret=SECRET_KEY, )
    i = (session.place_batch_order(
        category="linear",
        request=[{"category": "linear", "symbol": symbol, "orderType": "Limit", "side": side_lim, "qty": qty1,
                  'price': price1},
                 {"category": "linear", "symbol": symbol, "orderType": "Limit", "side": side_lim, "qty": qty2,
                  'price': price2},
                 {"category": "linear", "symbol": symbol, "orderType": "Limit", "side": side_lim, "qty": qty3,
                  'price': price3}, ]))
    mess = 'открыты 3 лимитных ордера для фиксации прибыли'
    print(mess)
    send_message(mess)
    print('пакетные лимитники= ', i)
    return price_list


def get_position(symbol):
    session = HTTP(
        testnet=False, api_key=API_KEY, api_secret=SECRET_KEY, )
    inf = (session.get_positions(category="linear", symbol=symbol, ))
    llist = inf['result']['list'][0]
    price_order = float(llist['avgPrice'])
    return price_order


def size_position(symbol):
    session = HTTP(
        testnet=False, api_key=API_KEY, api_secret=SECRET_KEY, )
    inf = (session.get_positions(category="linear", symbol=symbol, ))
    llist = inf['result']['list'][0]
    size = float(llist['size'])  # размер текущей позиции
    return size


def set_trading_stop(symbol, stop_loss):  # Будем передвигать стоп после закрытия 1/2 обьема лота
    print('Функция - set_trading_stop')
    session = HTTP(
        testnet=False, api_key=API_KEY, api_secret=SECRET_KEY, )
    print(session.set_trading_stop(
        category="linear",
        symbol=symbol,
        stopLoss=stop_loss,
        positionIdx=0, ))


def change_stop(symbol, side, stop_price, price_list):  # Ждем сработки первого тейка или стоп лосса
    print('Функция - change_stop')
    price_order = get_position(symbol)  # проверяем цену открытого ордера, на нее переставим стоп лосс
    price2 = float(price_list[0])  # цена первого тейка
    print(f'цена первого тейка {price2}')
    while True:
        last = order_book(symbol)
        position = size_position(symbol)
        print('side', side, ' текущая цена=', last)
        print(f'stop_loss={stop_price} второй тейк= {price2} размер позиции= {position}')
        if position == 0:
            cancel_all_orders(symbol)
            return 1
        if side == 'Sell' and last < price2:  # Если цена меньше первого тейка(т.е. тейк сработал)нужно перенести стоп в безубыток
            set_trading_stop(symbol, price_order)
            return 2
        if side == 'Buy' and last > price2:
            set_trading_stop(symbol, price_order)
            return 2
        if side == 'Sell' and last >= stop_price:  # Если сработалл стоп лосс
            i = cancel_all_orders(symbol)
            print('change_stop()', i)
            return 1
        if side == 'Buy' and last <= stop_price:  # Если сработалл стоп лосс
            i = cancel_all_orders(symbol)
            print('change_stop()', i)
            return 1
        time.sleep(1)


def check_orders(symbol, side,
                 price_list):  # Ждем когда цена дойдет до последнего тейка или до стоплосса.Закрываем открытые позиции
    count = 0
    print('Функция - check_orders')
    price_order = get_position(symbol)  # проверяем цену открытого ордера.и стоплосса (который на ней стоит)
    print('pricelist', price_list)
    price2 = float(price_list[2])  # цена последнего тейка
    print('price2', price2)
    while True:
        last = order_book(symbol)  # Последняя цена
        if count % 20 == 0:
            print(f'стоп-лосс= {price_order}  цена= {last}  тейк-профит= {price2}')
        if side == 'Buy':  # Если покупка
            if last < price_order:  # Сработал стоплосс
                cancel_all_orders(symbol)
                return 1
            if last > price2:  # Сработал тейк профит
                cancel_all_orders(symbol)
                return 2
        else:  # Если продажа
            if last > price_order:  # Сработал стоплосс
                cancel_all_orders(symbol)
                return 1
            if last < price2:  # Сработал тейк профит
                cancel_all_orders(symbol)
                return 2
        time.sleep(5)
        count += 1


def cancel_all_orders(symbol):
    print('Функция - cancel_all_orders')
    session = HTTP(
        testnet=False, api_key=API_KEY, api_secret=SECRET_KEY, )
    canc = (session.cancel_all_orders(
        category="linear",
        symbol=symbol, ))
    print(canc)
    mess = 'Отмена всех ордеров'
    print(mess)
    send_message(mess)


def get_open_orders(symbol):  # Возвращает лимитные и стопордера. Функция пока не используется
    print('Функция - get_open_orders')
    session = HTTP(testnet=False, api_key=API_KEY, api_secret=SECRET_KEY)
    inf = (session.get_open_orders(
        category="linear",
        symbol=symbol,
        openOnly=0,
        limit=20, ))
    llist = inf['result']['list']
    lenght = len(llist)  # Длина списка это кол-во отложенных ордеров
    mess = (f'кол-во отложенных ордеров {lenght}')
    if lenght > 0:
        for i in llist:
            price = i['price']
            qty = i['qty']
            print(f'price {price}  qty {qty}')
    return mess


def get_wallet():
    session = HTTP(testnet=False, api_key=API_KEY, api_secret=SECRET_KEY)
    ballance_row = (session.get_wallet_balance(
        accountType="UNIFIED",
        coin="USDT", ))
    marg_ballance = ballance_row['result']['list'][0]['totalMarginBalance']
    equity = float(ballance_row['result']['list'][0]['totalEquity'])

    print('equity= ', equity)
    return equity


def control(symbol, level):
    print('Функция - control')
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main(symbol, level))
    loop.run_until_complete(future)
    side, qty, qty_list, min_step, balance = future.result()
    asyncio.get_event_loop().stop()
    print(side, qty)
    stop_price = new_order(symbol, side, qty, level, min_step)  # Открываем новый ордер
    price_list = limit_order(symbol, side, level, qty_list)  # Открываем лимитники для фиксации прибыли
    print(f'price list {price_list}')
    i = change_stop(symbol, side, stop_price, price_list)  # Следим за позицией, если закрылась то
    print('функция контрол i= ', i)
    if i == 1:
        balance2 = get_wallet()
        bal_fin = round((balance2 - balance), 3)
        mess = f'{symbol} Сработал стоп лосс. Все лимитники закрыты. Убыток= {bal_fin}'
        print(mess)
        send_message(mess)
    else:
        balance2 = get_wallet()
        bal_fin = round((balance2 - balance), 3)
        mess = f'{symbol} Закрыта 1-я часть позиции.Стоп в безубытке.Частичная прибыль= {bal_fin}'
        print(mess)
        send_message(mess)
        res = check_orders(symbol, side, price_list)
        if res == 1:  # Сработал стоп лосс
            balance2 = get_wallet()
            bal_fin = round((balance2 - balance), 3)
            if bal_fin < 0:
                cancel_all_orders(symbol)
                mess_fin = f'{symbol} Сработал стоп лосс. Лимитник закрыт. Убыток= {bal_fin}'
                print(mess_fin)
                send_message(mess_fin)
            else:
                cancel_all_orders(symbol)
                mess_fin = f'{symbol} Сработал стоп лосс. Лимитник закрыт. Прибыль= {bal_fin}'
                print(mess_fin)
                send_message(mess_fin)
        else:
            balance2 = get_wallet()
            bal_fin = round((balance2 - balance), 3)
            mess_fin = f'{symbol} Последний тейк закрыт. Прибыль= {bal_fin}'
            print(mess_fin)
            send_message(mess_fin)


if __name__ == '__main__':
    print('Функция - if name')
    symbol = 'ETHUSDT'
    level = 2521.7  # Задать уровень
    direction = 1  # Направление
    control(symbol, level)

