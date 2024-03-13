# cd PycharmProjects\bybit_webs\venv\Scripts
# activate.bat      =>  big_candle_sell.py
# Ловля ножей   доработка knives.py
# Скрипт подключается к вебсокету без pybit. Делим данные по пять секунд.Ждем пробой уровня, высокий обьем и на
# пробое откатной свечи входим в сделку
# нарисовать на листе алгоритм что и за чем идет. Перестроить так чтобы переписать откатный уровень
# добавили переменную cross и модуль ситуации когда цена пробила уровень без обьема и вернулась под уровень

from config import API_KEY, SECRET_KEY, Bot, Chat_id
import websockets
import asyncio
import json
import time
import requests
from pybit.unified_trading import HTTP


async def main(symbol, level, direction, qty, check):
    print('функция - main')
    global list_count
    url = "wss://stream.bybit.com/v5/public/linear"
    subscription = {
        "op": "subscribe",
        "args": [f"publicTrade.{symbol}"]
    }

    while True:
        try:
            async with websockets.connect(url) as client:
                message = 'Начало скрипта'
                print(message)
                file_name = f'{time_sec()}'
                with open(f'{file_name}.txt', 'a') as file:
                    file.write(f'{message}\n')
                    file.write(f'{symbol}, {level} ,направление= {direction}, quantity={qty}\n')
                counter = -1
                sum_vol = 0
                old_period = -1
                candle_color = 0
                cross = 0
                llist_mass = []  # Список свечей OHLC
                llist = []  # Список цен в течении 5 сек
                await client.send(json.dumps(subscription))
                while True:
                    mass = json.loads(await client.recv())
                    data = mass.get('data')
                    if data != None:
                        for el in data:
                            # Получение основных данных
                            time_trade = (el['T'])
                            time_trade_sec = int(str(time_trade)[-5:-3])
                            price_trade = float(el['p'])
                            vol_trade = float(el['v'])

                            # Страховка если во время разрыва связи цена пробьет уровень
                            if counter == -1:  # Если в первом запросе цена уже выше уровня,то заканчиваем выполнение скрипта
                                print('counter=-1----')
                                if direction > 0 and price_trade > level:
                                    break
                                if direction < 0 and price_trade < level:
                                    break
                            counter += 1
                            llist.append(price_trade)

                            # Делим время на периоды по 5 сек
                            current_period = (time_trade_sec // 5) * 5
                            if sum_vol == 0:  # Определяем первую цену в свече
                                first_price_candle = price_trade
                            sum_vol += vol_trade

                            # ++++++++++++++++++++++++++++++++++ Открытие ордера ++++++++++++++++++++++++++++++++++++++
                            if check == 5 and price_trade > open_level_price:
                                mess = 'открываем ордер на покупку'
                                await send_message(mess)
                                print(mess)
                                stop_price = breakout_candle_parameters[0][2]
                                take_profit = open_level_price * 1.004
                                side = 'Buy'
                                with open(f'{file_name}.txt', 'a') as file:
                                    file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    file.write(f'{mess} side {side} stop= {stop_price},take= {take_profit}\n')
                                await new_order(symbol, side, qty, stop_price, take_profit)
                                check = 7

                            if check == 4 and price_trade < open_level_price:
                                mess = 'открываем ордер на продажу'
                                await send_message(mess)
                                print(mess)
                                stop_price = breakout_candle_parameters[0][1]
                                take_profit = open_level_price / 1.004
                                side = 'Sell'
                                with open(f'{file_name}.txt', 'a') as file:
                                    file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    file.write(f'{mess} side {side} stop= {stop_price},take= {take_profit}\n')
                                await new_order(symbol, side, qty, stop_price, take_profit)
                                check = 8
                            # ++++++++++++++++++++++++++++++++++ Открытие лимитки +++++++++++++++++++++++++++++++++++++
                            if check == 15:
                                mess = f'выставляем лимитку на покупку по цене{open_limit_price}'
                                await send_message(mess)
                                print(mess)
                                stop_price = open_limit_price - 8
                                take_profit = open_limit_price * 1.004
                                side = 'Buy'
                                with open(f'{file_name}.txt', 'a') as file:
                                    file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    file.write(f'{mess} side {side} stop= {stop_price},take= {take_profit}\n')
                                await new_limit_order(symbol, side, qty, open_limit_price, stop_price, take_profit)
                                check = 9# Временно. Позже дописать слежение до сработки и т.д.

                            if check == 14:
                                mess = f'выставляем лимитку на продажу по цене{open_limit_price}'
                                await send_message(mess)
                                print(mess)
                                stop_price = open_limit_price +8
                                take_profit = open_limit_price / 1.004
                                side = 'Sell'
                                with open(f'{file_name}.txt', 'a') as file:
                                    file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    file.write(f'{mess} side {side} stop= {stop_price},take= {take_profit}\n')
                                await new_limit_order(symbol, side, qty, open_limit_price, stop_price, take_profit)
                                check = 9# Временно. Позже дописать слежение до сработки и т.д.



                            # Начало нового 5-ти секундного периода
                            if old_period != current_period:
                                print('Начало нового 5-ти секундного периода')
                                minn = time.localtime().tm_min  # Получение текущего времени
                                secc = time.localtime().tm_sec

                                if minn == 0 and secc == 0:  # Начало нового часа
                                    print("Начало нового часа")  # Принтуем в начале каждого часа
                                openn = float(llist[0])
                                close = float(llist[-1])
                                llist.sort()
                                high = llist[-1]
                                low = llist[0]
                                print(f'openn={openn}  close={close}')
                                llist = []
                                if openn > close:
                                    candle_color = -1 # red
                                elif openn < close:
                                    candle_color = 1 # green
                                else: candle_color = 0 # none
                                print('candle_color=', candle_color,' sec=',secc, 'current_period=', current_period)
                                llist_mass.append([openn, high, low, close, int(sum_vol)]) # Добавляем в список параметры свечи
                                if len(llist_mass) > 30:  # Ограничивает список 30-ю свечками
                                    llist_mass = llist_mass[1:]
                                print(f'check={check}')

                                # Обработка данных первый заход ждем пробой уровня и высокий обьем
                                if check == 1 and sum_vol > 1000:# 2000 для ETH

                                    print(f'direction{direction} price_trade{price_trade} level{level} '
                                          f'candle_color={candle_color} sum_vol={sum_vol}')
                                    breakout_candle_parameters = []  # Параметры пробойной свечи
                                    breakout_candle_parameters.append([openn, high, low, close])
                                    print(breakout_candle_parameters)
                                    if direction > 0 and price_trade > level and candle_color > 0:
                                        mess = f'{symbol} зелёная длинная свеча, ждем откатную красную'
                                        print(mess)
                                        await send_message(mess)
                                        await asyncio.sleep(0.2)
                                        check = 2
                                    if direction < 0 and price_trade < level and candle_color < 0:
                                        mess = f'{symbol} красная длинная свеча, ждем откатную зеленую'
                                        print(mess)
                                        await send_message(mess)
                                        await asyncio.sleep(0.2)
                                        check = 3
                                #------------------------------------------------------------------------------------#
                                # Отрабатываем ситуацию когда цена пробила уровень без обьема и вернулась под уровень#
                                # Если цена пересекла уровень вверх и прошла еще 0,2%
                                if check == 1 and direction > 0 and price_trade > level*1.002:
                                    cross = 2# Пересечение вверх случилось

                                # Если цена пересекла уровень вниз и прошла еще 0,2%
                                if check == 1 and direction < 0 and price_trade < level/1.002:
                                    cross = 3  # Пересечение вниз случилось

                                if check == 1 and cross == 2 and price_trade < level/1.005:
                                    mess = 'цена вернулась под уровень заканчиваем работу скрипта'
                                    print(mess)
                                    with open(f'{file_name}.txt', 'a') as file:
                                        file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                    await send_message(mess)
                                    await asyncio.sleep(0.2)
                                    check = 9
                                if check == 1 and cross == 3 and price_trade > level/1.005:
                                    mess = 'цена вернулась над уровень заканчиваем работу скрипта'
                                    print(mess)
                                    with open(f'{file_name}.txt', 'a') as file:
                                        file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                    await send_message(mess)
                                    await asyncio.sleep(0.2)
                                    check = 9

                                # Обработка данных второй заход. Ждем откатную красную свечу
                                if check == 2:
                                    with open(f'{file_name}.txt', 'a') as file:
                                        file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    # Если сформирована откатная свеча, ждем цену ниже минимума и продаём
                                    if openn > close:
                                        if breakout_candle_parameters[0][1] - low < 8:
                                            open_level_price = low -1 # минимум откатной свечи
                                            with open(f'{file_name}.txt', 'a') as file:
                                                file.write(
                                                    f'time = {time_sec()} check = {check},сформирована откатная крвсная свеча'
                                                    f'будем открывать маркет\n')
                                            print(f'time = {time_sec()} check = {check},сформирована откатная крвсная свеча'
                                                    f'будем открывать маркет\n')
                                            check = 4 # Будем открывать маркет
                                        else:
                                            open_limit_price = breakout_candle_parameters[0][1] -7
                                            with open(f'{file_name}.txt', 'a') as file:
                                                file.write(
                                                    f'time = {time_sec()} check = {check},сформирована откатная красная свеча'
                                                    f'будем ставить лимитку\n')
                                            print(f'time = {time_sec()} check = {check},сформирована откатная красная свеча'
                                                    f'будем ставить лимитку\n')
                                            check = 14 # Будем открывать лимитку


                                # Обработка данных третий заход. Ждем откатную зеленую свечу
                                if check == 3:
                                    with open(f'{file_name}.txt', 'a') as file:
                                        file.write(f'time = {time_sec()} check = {check}, {breakout_candle_parameters}\n')
                                    # Если сформирована откатная свеча, ждем цену выше максимума и покупаем
                                    if openn < close:
                                        if high - breakout_candle_parameters[0][2] < 8:
                                            open_level_price = high +1 # максимум откатной свечи
                                            with open(f'{file_name}.txt', 'a') as file:
                                                file.write(
                                                    f'time = {time_sec()} check = {check},сформирована откатная зеленая свеча'
                                                    f'будем открывать маркет\n')
                                            print(f'time = {time_sec()} check = {check},сформирована откатная зеленая свеча'
                                                    f'будем открывать маркет\n')
                                            check = 5 # Будем открывать маркет
                                        else:
                                            open_limit_price = breakout_candle_parameters[0][2] + 7
                                            with open(f'{file_name}.txt', 'a') as file:
                                                file.write(f'time = {time_sec()} check = {check},сформирована откатная зеленая свеча'
                                                    f'будем ставить лимитку\n')
                                            print(f'time = {time_sec()} check = {check},сформирована откатная зеленая свеча'
                                                    f'будем ставить лимитку\n')
                                            check = 15  # Будем открывать лимитку


                                if check == 7: # Проследить за открытым ордером и по достижении стопа или тейка
                                    if price_trade > take_profit:
                                        mess = 'Сделка закрыта по тейку'
                                        print(mess)
                                        with open(f'{file_name}.txt', 'a') as file:
                                            file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                        await send_message(mess)
                                        check = 9
                                        return
                                    if price_trade < stop_price:
                                        mess = 'Сделка закрыта по стопу'
                                        print(mess)
                                        with open(f'{file_name}.txt', 'a') as file:
                                            file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                        await send_message(mess)
                                        check = 9
                                        return
                                if check == 8:
                                    if price_trade < take_profit:
                                        mess = 'Сделка закрыта по тейку'
                                        print(mess)
                                        with open(f'{file_name}.txt', 'a') as file:
                                            file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                        await send_message(mess)
                                        check = 9
                                        return
                                    if price_trade > stop_price:
                                        mess = 'Сделка закрыта по стопу'
                                        print(mess)
                                        with open(f'{file_name}.txt', 'a') as file:
                                            file.write(f'time = {time_sec()} check = {check}, {mess}\n')
                                        await send_message(mess)
                                        check = 9
                                        return

                                sum_vol = 0
                            old_period = current_period

                        if check == 9:  # Замените "условие" на ваше реальное условие
                            with open(f'{file_name}.txt', 'a') as file:
                                file.write(f'time = {time_sec()} check = {check}, выход из внутреннего цикла\n')
                            break  # Выход из внутреннего цикла
                        # Страховка от неправильного уровня выход из внешнего цикла
                        if counter == -1 and direction < 0 and price_trade < level:
                            break

                # Страховка от неправильного уровня выход из внешнего цикла
                if counter == -1 and direction < 0 and price_trade < level:
                    break
                if check == 9:
                    with open(f'{file_name}.txt', 'a') as file:
                        file.write(f'time = {time_sec()} check = {check}, выход из внешнего цикла\n')
                    break
        except Exception as e:
            print(f"Ошибка внутри main: {e}")
            print("Перезапуск скрипта через 15 секунд...")
            time.sleep(15)


def time_sec():
    loc_sec = time.localtime()
    data_time = time.strftime("%Y-%m-%d--%H-%M-%S", loc_sec)
    return data_time


async def new_order(symbol, side, qty, stop_price, take_profit):  # Открываем Новый ордер
    print('Функция - new_order')
    session = HTTP(testnet=False,
                   api_key=API_KEY,
                   api_secret=SECRET_KEY, )
    print(session.place_order(
        category="linear",
        symbol=symbol,  # "XRPUSDT"
        side=side,  # 'Buy' or 'Sell'
        orderType="Market",
        qty=qty,
        stopLoss=stop_price,
        takeProfit=take_profit))
    return stop_price


async def new_limit_order(symbol, side, qty, open_limit_price, stop_price, take_profit):  # Выставляем лимитный ордер
    print('Функция - new_order')
    session = HTTP(testnet=False,
                   api_key=API_KEY,
                   api_secret=SECRET_KEY, )
    print(session.place_order(
        category="linear",
        symbol=symbol,  # "XRPUSDT"
        price=open_limit_price,
        side=side,  # 'Buy' or 'Sell'
        orderType="Limit",
        qty=qty,
        stopLoss=stop_price,
        takeProfit = take_profit))
    return stop_price


async def send_message(mess):
    bot = Bot
    chat_id = Chat_id
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    params = {'chat_id': chat_id, 'text': mess}
    resp = requests.post(url, data=params)
    print('resp', resp)


def send_message2(mess):
    bot = Bot
    chat_id = Chat_id
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    params = {'chat_id': chat_id, 'text': mess}
    resp = requests.post(url, data=params)
    print('resp', resp)


def get_wallet():
    session = HTTP(testnet=False, api_key=API_KEY, api_secret=SECRET_KEY)
    ballance_row = (session.get_wallet_balance(
        accountType="UNIFIED",
        coin="USDT", ))
    print(ballance_row)
    equity = float(ballance_row['result']['list'][0]['totalEquity'])
    print('equity= ', equity)
    return equity


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


def control(symbol, level, direction,qty, check):
    print('Функция - control')
    balance = get_wallet()
    print(f'balance= {balance}')
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main(symbol, level, direction, qty, check))
    loop.run_until_complete(future)
    asyncio.get_event_loop().stop()
    balance_new = get_wallet()
    balance_dir = balance_new - balance
    if balance_dir>0:
        mess = f'Прибыль = {balance_dir}'
        print(mess)
        send_message2(mess)
    else:
        mess = f'Убыток = {balance_dir}'
        print(mess)
        send_message2(mess)
    cancel_all_orders(symbol)


if __name__ == '__main__':
    print('Функция - if name')
    symbol = 'ETHUSDT'
    level = 3410 # Задать уровень
    direction = -1  # Направление в сторону уровня на котором ждем закол
    qty = 0.01 # Задать обьем
    check = 1
    control(symbol, level, direction, qty, check)
