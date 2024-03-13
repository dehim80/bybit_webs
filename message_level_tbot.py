# Выставляем пару и уровень. Получаем сообщение в телеграм при пересечении
from config import Chat_id, Bot
import websocket
import threading
import _thread
import json
import time
import datetime
from functools import partial
import requests


symbol = 'ETHUSDT'
level = 1775.72
direction = -1
counter = -1
old_millisec = -1


def on_open(ws):
    print('Websocket was opened')
    def run(*args):
        tradeStr = {'op': 'subscribe', 'args': params}
        ws.send(json.dumps(tradeStr))
    _thread.start_new_thread(run, ())


def on_message(ws, msg, symbol, direction):  # information processing here
    global old_millisec
    global counter

    mass = json.loads(msg)
    data = mass['data']
    for el in data:
        data_price = float(el['p'])
        data_unixtime = el['T']
        now_millis = data_unixtime % 1000
        print(f'now_millis = {now_millis} counter={counter} price={data_price} level/dir {level} / {direction}')
        if now_millis < old_millisec: # Начало новой секунды
            if counter > 300 and direction > 1 and data_price > level: # Если движение вверх
                mess = f'time {conv_un_time(now_millis)} price={data_price}'
                send_message(mess)
            if counter > 300 and direction < 1 and data_price < level:
                mess = f'time {conv_un_time(data_unixtime)} price={data_price} '
                send_message(mess)
            print(f'Начало новой минуты oldmillis={old_millisec}  now_millis={now_millis}')
            counter = 0
        old_millisec = now_millis
        counter += 1


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


def on_error(ws, error):
    print('Error', error)


def on_close(ws, close_status_code, close_msg):
    print('Closing')
    print('ждем 30 секунд для дальнейшего подключения')
    time.sleep(30)
    connect_to_websocket()


def send_message(mess):
    bot = Bot
    chat_id = Chat_id
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    params = {'chat_id': chat_id, 'text': mess}
    resp = requests.post(url, data=params)
    print('resp', resp)


def unsubscribe_from_data(ws, params):
    unsubscribe_str = {'op': 'unsubscribe', 'args': params}
    ws.send(json.dumps(unsubscribe_str))


def connect_to_websocket():
    socket_conn = websocket.WebSocketApp(url=url, on_open=on_open, on_message=on_message_partial, on_error=on_error,
                                         on_close=on_close, )
    thread = threading.Thread(target=socket_conn.run_forever)
    thread.start()


url = 'wss://stream.bybit.com/v5/public/linear'
params = [f'publicTrade.{symbol}']
on_message_partial = partial(on_message, symbol=symbol, direction=direction)
connect_to_websocket()
