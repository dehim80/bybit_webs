# cd PycharmProjects\bybit_webs\venv\Scripts
# activate.bat      => python stop_loss_calculation.py
import requests
from pybit.unified_trading import HTTP

# Затем меняем этот параметр до подходящего уровня убытка
coef_list={'BTCUSDT':0.5,'ETHUSDT':0.6,'1000PEPEUSDT':0.3,'BCHUSDT':1,'LTCUSDT':0.16,'LINKUSDT':0.2,'MDTUSDT':1,
            'AVAXUSDT':1,'BNBUSDT':1,'XRPUSDT':1,'MATICUSDT':1,'COMPUSDT':1,'APTUSDT':0.18,'OPUSDT':1,
            'FILUSDT':1,'SUIUSDT':0.18,'ARBUSDT':0.3,'SOLUSDT':1,'WLDUSDT':1,'AUCTIONUSDT':0.2,'ETHWUSDT':0.15}


# ДЛИННАЯ ПОЗИЦИЯ / Сначала меняем этот параметр, до уровня подходящего стоп лосса
# При уменьшении уменьшается стоп.2529
pair_list ={'BTCUSDT':0.005,'ETHUSDT':0.003,'1000PEPEUSDT':0.004,'BCHUSDT':0.002,'LTCUSDT':0.015,'LINKUSDT':0.01,'MDTUSDT':0.002,
            'AVAXUSDT':0.004,'BNBUSDT':0.002,'XRPUSDT':0.003,'COMPUSDT':0.004,'APTUSDT':0.007,'OPUSDT':0.008,'FILUSDT':0.002,
            'SUIUSDT':0.02,'ARBUSDT':0.006,'SOLUSDT':0.002,'WLDUSDT':0.005,'AUCTIONUSDT':0.008,'ETHWUSDT':0.007}



sum = 210

def stop_loss(symbol, level, side):
    global sum
    global pair_list
    sum = sum * (coef_list[f'{symbol}'])
    min_step =min_stepp(symbol)
    coef=pair_list[f'{symbol}']
    print(f'coef {coef}')
    if side == 1:
        stop = level - (level*coef)
        stop = stop - (stop % min_step)
        comission = sum * 0.0006 * 2
        lot = sum / level  # расчитываем лот. Сумма на счете/цену актива
        not_form_round_lot = lot - (lot % min_lot(symbol))  # таким лотом будет открыта сделка
        round_lot_str = '{:.10f}'.format(not_form_round_lot)
        round_lot = float(round_lot_str)
        sum_open_order = round_lot * level
        result = (sum_open_order)-(round_lot * stop)
        result_with_com = result + comission
        mess = f'stop-loss= {stop} Потери в деньгах= {result} + комиссия = {result_with_com}' \
               f'\nколичество лотов= {round_lot}'
        print(mess)
        return stop
    else:
        stop = level + (level*coef)
        stop = stop - (stop % min_step)
        comission= sum*0.0006*2
        lot = sum / level  # расчитываем лот. Сумма на счете/цену актива
        not_form_round_lot = lot - (lot % min_lot(symbol))  # таким лотом будет открыта сделка
        round_lot_str = '{:.10f}'.format(not_form_round_lot)
        round_lot = float(round_lot_str)
        sum_open_order = round_lot*level
        result = (round_lot*stop)-(sum_open_order)
        result_with_com = result+comission
        mess = f'stop-loss= {stop} Потери в деньгах= {result} + комиссия = {result_with_com}' \
               f'\nколичество лотов= {round_lot}'
        print(mess)
        return stop
    pass


def min_lot(symbol): # Функция вычисляет минимальный лот
    print('Функция - min_lot')
    global sum
    session = HTTP(testnet=False)
    inf = (session.get_instruments_info(
        category="linear",
        symbol=symbol))
    min_step = float(inf['result']['list'][0]['priceFilter']['tickSize'])# найти минимальный шаг символа и при расчете стоп лосса округлять до него
    min_lot = float(inf['result']['list'][0]['lotSizeFilter']['minOrderQty'])
    print('min lot= ', min_lot)
    return min_lot


def min_stepp(symbol): # Функция возвращает минимальный лот
    print('Функция - min_lot')
    session = HTTP(testnet=False)
    inf = (session.get_instruments_info(
        category="linear",
        symbol=symbol,
    ))
    min_step = float(inf['result']['list'][0]['priceFilter']['tickSize'])
    return min_step


if __name__ == '__main__': # нужно написать словарь{ символ: изменение за секунду}для всех пар для MDT:20
    print('Функция - if name')
    symbol = 'ETHUSDT'
    level = 2444 # Задать уровень
    direction = 1 # Направление
    stop_loss(symbol, level, direction)
