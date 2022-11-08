import sys

from iqoptionapi.stable_api import IQ_Option
import logging
from datetime import datetime, timedelta
from colorama import init, Fore, Back
from time import time

import numpy as np
from talib.abstract import *


init(autoreset=True)


logging.disable(level=(logging.DEBUG))

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

    print('\n\nDigite a Paridade: ')
    par = str(input().strip()).upper()

    print('\nTimeFrame: ')
    timeframe = int(input())

    print('\nPeriodo de velas: ')
    qtd_velas = int(input())

    while True:
        inicio = time()
        velas = Iq.get_candles(par, timeframe, qtd_velas, time())

        dados_f = {
            'open': np.empty(qtd_velas),
            'high': np.empty(qtd_velas),
            'low': np.empty(qtd_velas),
            'close': np.empty(qtd_velas),
            'volume': np.empty(qtd_velas),
        }

        for x in range(0, qtd_velas):
            dados_f['open'][x] = velas[x]['open']
            dados_f['high'][x] = velas[x]['max']
            dados_f['low'][x] = velas[x]['min']
            dados_f['close'][x] = velas[x]['close']
            dados_f['volume'][x] = velas[x]['volume']

        up, mid, low = BBANDS(dados_f, timeperiod=5, nbdevup=2.0, nbdevdn=2.0, matype=0)

        up = round(up[len(up) - 2], 5)
        low = round(low[len(low) - 2], 5)
        taxa_atual = round(velas[-1]['close'], 5)

        print('Taxa: ', taxa_atual,
              '| UP: ', up,
              '| LOW: ', low,
              '| Time: ', round(time() - inicio, 2), 'seg'
              '| TVela: ', datetime.fromtimestamp(int(velas[-1]['from'])).strftime('%H:%M')
              )

        if taxa_atual >= up or taxa_atual <= low:
            print('\n Realizando entrada na taxa: ', taxa_atual)

            status, id = Iq.buy_digital_spot(par, 2.0, 'put' if taxa_atual >= up else 'call', timeframe)

            if status:
                print('\n Entrada realizada com sucesso, aguardando resultado...')

                while True:
                    status, valor = Iq.check_win_digital_v2(id)

                    if status:
                        if valor < 0 : valor = -2

                        print('\n\n Resultado da operação: ', end='')
                        if valor > 0: print('WIN: ',valor)
                        else: print('LOSS: ',valor)

                    break

                print('\n',50*'-')


except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")