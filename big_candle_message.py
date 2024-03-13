# cd PycharmProjects\bybit_webs\venv\Scripts
# activate.bat      =>  knives.py
#*******************  Если пробит уровень и свеча больше 19п- посылает message в телеграм *************************
# Скрипт подключается к вебсокету без pybit. Делим данные по пять секунд.За эти секунды изменение  цены
# должно быть выше обозначенного. Посылает сигнал в телеграмм


from config import Chat_id, Bot
import websockets
import asyncio
import json
import time
import requests


async def main(symbol, level):
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
                print('Начало скрипта')
                counter = -1
                sum_vol = 0
                old_period = -1
                llist_mass = [] # Список свечей OHLC
                llist = [] # Список цен в течении 5 сек
                await client.send(json.dumps(subscription))
                while True:
                    mass = json.loads(await client.recv())
                    data = mass.get('data')
                    if data != None:
                        for el in data:
                            time_trade = (el['T'])
                            time_trade_sec = int(str(time_trade)[-5:-3])
                            price_trade = float(el['p'])

                            llist.append(price_trade)
                            vol_trade = float(el['v'])
                            current_period = (time_trade_sec // 5) * 5
                            if sum_vol == 0:# Первая цена в свече
                                first_price_candle = price_trade
                            dif_price = abs(first_price_candle-price_trade)
                            sum_vol += vol_trade

                            if old_period != current_period:# Начало нового периода
                                minn = time.localtime().tm_min  # Получение текущего времени
                                secc = time.localtime().tm_sec
                                if minn == 0 and secc == 0:  # Проверка, начался ли новый час
                                    print("Начало нового часа") # Чтобы понимать что скрипт работает
                                open = float(llist[0])
                                close = float(llist[-1])
                                llist.sort()
                                high = llist[-1]
                                low = llist[0]
                                llist_mass.append([open, high, low, close, int(sum_vol)])# Добавляем в список свечу
                                if len(llist_mass) > 30:
                                    llist_mass = llist_mass[1:] # Ограничивает список 30-ю свечками

                                # Если длина свечи больше 19п и свеча красная
                                if dif_price > 0.0019 and first_price_candle > price_trade:#XRP 0.0019
                                    # Смотрим в массив со свечами чтобы минимумы были выше price_trade, чтобы
                                    # наша свеча не оказалась в середине диапазона
                                    print('мы в цикле  свеча красная')
                                    llist_mass.pop()
                                    print('llist_mass ', llist_mass)
                                    success = all(loww > price_trade for _, _, loww, _, _ in llist_mass)
                                    if success:
                                        mess = 'XRP красная длинная свеча'
                                        print(mess)
                                        send_message(mess)
                                # Если длина свечи больше 19п и свеча зеленая
                                if dif_price > 0.0019 and first_price_candle < price_trade:  # Зеленая свеча
                                    print('мы в цикле  Зеленая свеча')
                                    llist_mass.pop()
                                    print('llist_mass ',llist_mass)
                                    success = all(highh < price_trade for _, highh, _, _, _ in llist_mass)
                                    if success:
                                        mess = 'XRP зеленая длинная свеча'
                                        print(mess)
                                        send_message(mess)
                                sum_vol = 0
                            old_period = current_period
        except Exception as e:
            print(f"Ошибка внутри main: {e}")
            print("Перезапуск скрипта через 15 секунд...")
            time.sleep(15)


def send_message(mess):
    bot = Bot
    chat_id = Chat_id
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    params = {'chat_id': chat_id, 'text': mess}
    resp = requests.post(url, data=params)
    print('resp', resp)


def control(symbol, level):
    print('Функция - control')
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main(symbol, level))
    loop.run_until_complete(future)
    side, qty, qty_list, min_step, balance = future.result()
    asyncio.get_event_loop().stop()
    print(side, qty)


if __name__ == '__main__':
    print('Функция - if name')
    symbol = 'XRPUSDT'
    level = 9.4220  # Задать уровень
    direction = -1  # Направление
    control(symbol, level)
