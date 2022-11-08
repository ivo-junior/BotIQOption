import sys

from iqoptionapi.stable_api import IQ_Option
import logging
import time
import datetime as dt
import getpass
import json, configparser
from datetime import datetime, timedelta
from dateutil.tz import gettz
from six import b
from colorama import init, Fore, Back  # instalar biblioteca


from model.operaçao_model import Operation
from cryptography.fernet import Fernet

init(autoreset=True)

asset = "EURUSD"
maxDic = 10
size = 300


logging.disable(level=(logging.DEBUG))


MODE = 'PRACTICE'  # /"REAL"
ticks = []

def perfil():
    perfil = json.loads(json.dumps(Iq.get_profile_ansyc()))
    return perfil['result']

def times_tamp_convertter(x):
    horario = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    horario = horario.replace(tzinfo=gettz('GMT'))

    return str(horario.astimezone(gettz('America/Sao Paulo')))[:-6]

def balanco():
    banca = Iq.get_balance()
    return banca


def get_ticker_stream(time_frame, par):
    maxdic = 5
    Iq.start_candles_stream(par, time_frame, maxdic)
    time.sleep(1)
    candles = Iq.get_realtime_candles(par, time_frame)
    global ticks
    for candle in candles:
        cand = candles[candle]
        cdHandle = {}
        if "open" in cand:
            cdHandle['open'] = cand["open"]
            cdHandle['high'] = cand["max"]
            cdHandle['low'] = cand["min"]
            cdHandle['close'] = cand["close"]
            cdHandle['created_at'] = dt.datetime.fromtimestamp(cand["from"]).isoformat()
            cdHandle['timestamp'] = cand["from"]
            cdHandle['volume'] = cand["volume"]
            if any(str(tick['created_at']) == str(cdHandle['created_at']) for tick in ticks):
                pass
            else:
                ticks.append(cdHandle)

# Retorna 2 mil velas anteriores
def get_historical_candles(time_frame, par):
    endFromTime = time.time()
    for i in range(2):
        candles = []
        candles = Iq.get_candles(par, int(time_frame), 1000, endFromTime)
        cds = []
        for candle in candles:
            cdHandle = {}
            if candle["open"]:
                cdHandle['open'] = candle["open"]
                cdHandle['high'] = candle["max"]
                cdHandle['low'] = candle["min"]
                cdHandle['close'] = candle["close"]
                cdHandle['created_at'] = dt.datetime.fromtimestamp(candle["from"]).isformat()
                cdHandle['timestamp'] = candle["from"]
                cdHandle['volume'] = candle["volume"]
                cds.append(cdHandle)
        global ticks
        ticks = cds + ticks
        endFromTime = int(cds[0]["timestamp"]) - 1

# Retorna um dicionorio com todos os pares, no formato => par : id
def get_pares_id():
    pares = dict([(l, u) for u, l in Iq.get_all_ACTIVES_OPCODE().items()])

    return pares

def indicador_sentimento(paridade):
    Iq.start_mood_stream(paridade)

    while True:
        x = Iq.get_all_traders_mood()
        id = get_pares_id()
        for i in x:
            print(id[i]+': '+str(int(100 * round(x[i], 2))), end=' ')

# for par in get_paridades_per_maerket(paridades, 'turbo'):
#     payout(par, 'digital')
def payout(par, tp_market, timeframe_in_min=1):
    if tp_market == 'turbo':
        a = Iq.get_all_profit()
        return int(100 * a[par]['turbo'])
    elif tp_market == 'digital':
        Iq.subscribe_strike_list(par, timeframe_in_min)
        while True:
            d = Iq.get_digital_current_profit(par, timeframe_in_min)
            if d != False:
                d = int(d)
                break
            time.sleep(1)
        Iq.unsubscribe_strike_list(par, timeframe_in_min)
        return d

# paridades = Iq .get_all_open_time()
# get_paridades_per_maerket(paridades, 'turbo')
def get_paridades_per_market(dic_ativos, tp_market):

    digital = []
    binary_turbo = []

    if tp_market == 'turbo':
        for par_turbo in dic_ativos['turbo']:
            if dic_ativos['turbo'][par_turbo]['open'] == True:
                binary_turbo.append(par_turbo)
        return binary_turbo

    elif tp_market == 'digital':
        for par_digital in dic_ativos['digital']:
            if dic_ativos['digital'][par_digital]['open'] == True:
                digital.append(par_digital)
        return digital

def get_par_pagando_mais(timeframe = 1):
    paridades = Iq.get_all_open_time()
    digitais = get_paridades_per_market(paridades, 'digital')
    pay = []
    binarias = get_paridades_per_market(paridades, 'turbo')
    for d in digitais:
        pay.append({str(d): payout(d, 'digital', timeframe)})

    for b in binarias:
        pay.append({str(b): payout(b, 'turbo', timeframe)})


# get_history_operations_perfil('turbo-option', 10)
# dt_in e dt_fn indicam o momento para pegar o historico. 0 indica o momento atual
def get_history_operations_perfil(tp_market_history, qtd_operations, dt_in=0, dt_fn=0):
    status, historico = Iq.get_position_history_v2(tp_market_history, qtd_operations, 0, dt_in, dt_fn)

    ls_history = []

    if tp_market_history == 'digital-option':
        for h in historico['positions']:
            op = Operation(str(times_tamp_convertter(h['open_time'] / 1000)),
                           str(times_tamp_convertter(h['close_time'] / 1000)), str(h['invest']),
                           str(h['close_profit'] if h['close_profit'] == 0 else h['close_profit'] - h['invest']),
                           str(h['raw_event']['buy_amount']), str(h['raw_event']['instrument_underlying']),
                           str(h['raw_event']['instrument_dir']))
            ls_history.append(op)
        return ls_history

    elif tp_market_history == 'turbo-option':
        for h in historico['positions']:
            op = Operation(str(times_tamp_convertter(h['open_time'] / 1000)),
                           str(times_tamp_convertter(h['close_time'] / 1000)), str(h['invest']),
                           str(h['close_profit'] if h['close_profit'] == 0 else h['close_profit'] - h['invest']),
                           str(h['raw_event']['buy_amount']), str(h['raw_event']['active']),
                           str(h['raw_event']['direction']))
            ls_history.append(op)
        return ls_history

def entrada_binaria(paridade, valor, direcao, timeframe_in_min):
    status, id = Iq.buy(valor, paridade, direcao, timeframe_in_min)

    return status, id

def get_result_bin(status, id):
    if status:
        resultado, lucro = Iq.check_win_v4(id)
    return resultado, lucro

def entrada_digital(paridade, valor, direcao, timeframe_in_min):
    status, id = Iq.buy_digital_spot(paridade, valor, direcao, timeframe_in_min)

    return id, status

def get_result_digital(id, status):
    if status:
        while True:
            status, lucro = Iq.check_win_digital_v2(id)
            if status:
                if lucro > 0:
                    return lucro
                else:
                    return 0

# Vendendo operaçoes
# Iq.close_digital_option(id) ====> Pra vender na Digital. Aq só retorna o status da operaçao finalizada
# Iq.sell_option(id) ====> Pra vender na binaria. Aq retorna um dicionario de dados com infos da operaçao finalizada

# Usando Thread
# import threading
# threading.Thread(target=get_result_digital, args=('id_entrada', )).start()

# Usando Multiproencing
# Muito parecido com a Thread so que no multiprocessing vai usar realmente os multiprocessos da maquina,
# e nao da para encontrar um objeito de um processo em outro.

def pessoaEn(pessoa):
    key = Fernet.generate_key()
    f = Fernet(key)
    token = f.encrypt(pessoa.encode())

    return {'token': token.decode(), 'key': key.decode()}


def pessoaDe(persson, k):
    f = Fernet(k)
    token = f.decrypt(persson)

    return token.decode()

def configuracao():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')
    return {'lo': arquivo.get('login', 'u').replace('\'','"'), 's': arquivo.get('login', 's').replace('\'','"'), 'entrada': arquivo.get('parametros', 'valor_entrada'), 'mg': arquivo.get('parametros', 'qtd_mg'), 'loss': arquivo.get('parametros', 'stop_loss'), 'gain': arquivo.get('parametros', 'stop_gain'), 'modo': arquivo.get('parametros', 'modo_conta')}

def auto_martingale(tipo, valor_ini, payout, valor_perca):
    if tipo == 'simples':
        return round(valor_ini * 2.2)
    elif tipo == 'lucro':
        lucro_esperado = valor_ini * payout
        while True:
            if round(valor_ini * payout, 2) > round(abs(valor_perca) + lucro_esperado, 2):
                return round(valor_ini, 2)
                break
            valor_ini += 0.01
    else:
        while True:
            if round(valor_ini * payout, 2) > round(abs(valor_perca), 2):
                return round(valor_ini, 2)
                break
            valor_ini += 0.01

# Para usar como recuperaçao + lucro de 2 niveis de soros
def soros_gale(valor_ini, payout, valor_perca):
    lucro_esperado = valor_ini * payout
    while True:
        if round(valor_ini * payout, 2) > round(abs(valor_perca) + lucro_esperado, 2):
            return round(valor_ini, 2) / 2
            break
        valor_ini += 0.01

def stop(lucro_total, gain, loss):
    if lucro_total <= float('-' + str(abs(loss))):
        print('Stop LOSS Atingido! Finalizando o bot...')
        sys.exit()
    if lucro_total >= float(str(gain)):
        print('Stop GAIN Atingido!')
        sys.exit()

# -----------------EXTRATEGIAS--------------
# def mhi(par, qtd_velas, tem_sec=60):
def mhi(velas):
#     iniciando análise
    while True:
        minutos = float(((datetime.now()).strftime('%M.%S'))[1:])
        # 4.58 delay, para adiantar a entrada
        entrar = True if (minutos >= 4.58 and minutos <= 5) or minutos >= 9.58 else False

        if entrar:
            dir =  False

            # velas = Iq.get_candles(par, tem_sec, qtd_velas, time.time())

            velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
            velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
            velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'

            cores = velas[0] + ' ' + velas[1] + ' ' + velas[2]

            # Aqui ele esta comprando na minoria de velas---> 2 r e 3 g ele entra pra put
            if cores.count('g') > cores.count('r') and cores.count('d') == 0:
                return 'put'
                break
            if cores.count('r') > cores.count('g') and cores.count('d') == 0:
                return 'call'
                break
            # Aqui ele esta comprando na maioria de velas---> 2 g e 3 r ele entra pra put
            # if cores.count('g') > cores.count('r') and cores.count('d') == 0:
            #     return 'call'
            #     break
            # if cores.count('r') > cores.count('g') and cores.count('d') == 0:
            #     return 'put'
            #     break

# Indicadores da Iq

def indicadores_iq(ativo, time_frame=1):
    result_indicadores = Iq.get_technical_indicators(ativo)

    if result_indicadores['code'] == "no_technical_indicator_available" or result_indicadores['message'] == "Active is not supported: active id 'ACTIVE_ID_PASSED'":
        return 'Ativo não esta ativo no momento!'

    ind = {}

    for dados in result_indicadores:
        if dados['candle_size'] == (time_frame*60):
            ind.update({dados['name']})


# par = 'EURUSD'
# Iq.start_candles_stream(par, 60, 1)
# update = 0
# while True:
#     if update == 60: sr = get_sr()
#
#     candles = Iq.get_realtime_candles(par, 60)
#
#     for x in candles:
#         if candles[x]['close'] == sr['s1'] or candles[x]['close'] == sr['s2'] or candles[x]['close'] == sr['s3']: print('call')
#         if candles[x]['close'] == sr['r1'] or candles[x]['close'] == sr['r2'] or candles[x]['close'] == sr['r3']: print('put')
#
#         break
#     update +=1
#     time.sleep(1)
#
def get_sr(ativo, time_frame=1):
    result_indicadores = Iq.get_technical_indicators(ativo)

    if result_indicadores['code'] == "no_technical_indicator_available" or result_indicadores['message'] == "Active is not supported: active id 'ACTIVE_ID_PASSED'":
        return 'Ativo não esta ativo no momento!'

    sr = {}

    for dados in result_indicadores:
        if dados['candle_size'] == (time_frame*60):
            sr.update({ dados['name'].replace('Classic ', ''): dados['value'] })

    return sr


def best_payout(par, timeframe = 1):
    par = par.upper()

    tb = Iq.get_all_profit()
    Iq.subscribe_strike_list(par, timeframe)

    tentativas = 0

    while True:
        d = Iq.get_digital_current_profit(par, timeframe)

        if d != False:
            d = int(d)
            break
        time.sleep(1)

        if tentativas == 5:
            print("Nao foi possivel carregar payout")
            d = 0
            break
        tentativas+=1
    Iq.unsubscribe_strike_list(par,timeframe)

    payout = {'binario': 0, 'digital': d}

    payout['binario'] = int(100 * tb[par]['turbo']) if timeframe < 5 else int(100 * tb[par]['binary'])

    return 'binario' if payout['binario'] > payout['digital'] else 'digital'


def cataloga(par, dias, prct_call, prct_put, timeframe=1):
    data = []
    datas_testadas = []
    sair = False
    time_ = time()


    while sair == False:
        velas = Iq.get_candles(par, (timeframe *60), 1000, time_)
        velas.reverse()

        for x in velas:
            if datetime.fromtimestamp(x['from']).strftime('%Y-%m-%d') not in datas_testadas:
                datas_testadas.append(datetime.fromtimestamp(x['from']).strftime('%Y-%m-%d'))

            if len(datas_testadas) <= dias:
                x.update({'cor': 'verde' if x['open'] < x['close'] else 'vermerlha' if x['open'] == x['close'] else 'doji'})
                data.append(x)

            else:
                sair = True
                break
        time_ = int(velas[-1]['from'] -1)

    analise = {}
    for velas in data:
        horario = datetime.fromtimestamp(velas['from']).timestamp('%H:%M')

        if horario not in analise:
            analise.update({horario: {'verde': 0, 'vermelha': 0, 'doji': 0, '%': 0, 'dir': ''}})

        analise[horario][velas['cor']] += 1

        try:
            analise[horario]['%'] = round(100 * (analise[horario]['verde'] / analise[horario]['verde'] + analise[horario]['vermelha'] + analise[horario]['doji']))

        except:
            pass
    for horario in analise:
        if analise[horario]['%'] > 50 : analise[horario]['dir'] == 'CALL'
        if analise[horario]['%'] < 50 : analise[horario]['dir'] == 'CALL', analise[horario]['%'] == 'PUT', (100 -analise[horario]['%'])

    return analise

# Execução do bot
try:
    tryLogin = 0
    Iq = {}
    conteudo = open('config.txt').readlines()
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')
    fez_login = False
    config = configuracao()
    if arquivo.get('login', 'u') != '' or arquivo.get('login', 's') != '':
        fez_login = True
    if fez_login == False:
        status = False
        print("\n\nInforme Usuário e senha para iniciar\n")
        # conteudo.append('\n123 = 123')
        while status == False and tryLogin < 3:
            username = input("Usuário:")
            password = getpass.getpass("Senha:")
            Iq = IQ_Option(username, password)
            tryLogin += 1
            status, reason = Iq.connect()
            if status == False:
                res = json.loads(reason)
                if "code" in res and res["code"] == "invalid_credentials":
                    print("\n\nErro ao conectar! Usuário ou senha incorretos.\n\n")
                else:
                    print("\n\nErro ao tentar se conectar:" + res["message"] +"\n\n")
            else:
                break
        if status == False:
            raise ValueError("Você Excedeu 3 tentativas de login. Por favor tente novamente mais tare!")
        conteudo.append('\nu = '+str(pessoaEn(username)))
        conteudo.append('\ns = ' + str(pessoaEn(password)))
        arquivo = open('config.txt', 'w')
        arquivo.writelines(conteudo)
        arquivo.close()
    else:
        t1 = json.loads(config['lo'])['token']
        k1 = json.loads(config['lo'])['key']
        t2 = json.loads(config['s'])['token']
        k2 = json.loads(config['s'])['key']
        Iq = IQ_Option(pessoaDe(t1.encode(), k1.encode()), pessoaDe(t2.encode(), k2.encode()))
        Iq.connect()

    print("Conectado com sucesso!")

    valor_entrada = json.loads(config['entrada'])
    qtd_mg = json.loads(config['mg'])
    stop_loss = json.loads(config['loss'])
    stop_gain = json.loads(config['gain'])
    modo_conta = json.loads(config['modo'])

    rodando = True
    Iq.change_balance(MODE)

    is_paridade = input("\n\nDeseja a seleção automatica de paridades (y=sim | n=nao)? ").upper()
    if is_paridade == 'N':
        paridade = input("\nInforme a Paridade que deseja operar: ").upper()
    else:
        print("Pegando paridade com maior payout...")
    # print('Paridade: '+str(asset)+'/ Payout Digital: '+str(payout(asset, 'digital')))
    # print('Paridade: ' + str(asset) + '/ Payout Turbo: ' + str(payout(asset, 'turbo')))
    # while rodando:
    #     try:
    #         get_ticker_stream(5, asset)
    #         print('Tick: '+str(ticks))
    #         time.sleep(1)
    #     except Exception as e:
    #         print("Server ERROR - Await 5 seconds.: " + str(e))
    #         time.sleep(3)
    #         pass


except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")
