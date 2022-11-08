import configparser
import getpass
import json
import sys

import Fernet as Fernet
from iqoptionapi.stable_api import IQ_Option
import logging
from datetime import datetime, timedelta
from colorama import init, Fore, Back
from time import time


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

    while True:
        win = 0
        loss = 0
        doji = 0
        mg1 = 0
        mg2 = 0

        print('\n\nQual paridade deseja catalogar? ', end='')
        par = str(input().strip()).upper()

        print('\nQual TimeFrame deseja analizar? ', end='')
        timeframe = int(input())

        print('\nQual periodo(qtd velas) deseja analizar? ', end='')
        qtdVelas = int(input())

        candles = Iq.get_candles(par, timeframe, qtdVelas, int(time()))

        for index, vela in enumerate(candles):
            min = int(datetime.fromtimestamp(int(vela['from'])).strftime('%M')[1:])

            if min == 5 or min == 0:

                cor_operacao = 'g' if vela['open'] < vela['close'] else 'r' if vela['open'] > vela['close'] else 'd'

                entrada_analise = [
                    'g' if candles[index - i]['open'] < candles[index - i]['close'] else 'r' if candles[index - i]['open'] > candles[index - i]['close'] else 'd' for i in range(1, 4)
                ]
                entrada_analise = False if entrada_analise.count('d') > 0 else 'g' if entrada_analise.count('r') > entrada_analise.count('g') else 'r' if entrada_analise.count('g') > entrada_analise.count('r') else False

                if entrada_analise != False:

                    if entrada_analise == cor_operacao:
                        win +=1

                    else:
                        try:
                            mg1_res = 'g' if candles[index + 1]['open'] < candles[index + 1]['close'] else 'r' if candles[index + 1]['open'] > candles[index + 1]['close'] else 'd'
                        except:
                            mg1_res = False
                        try:
                            mg2_res = 'g' if candles[index + 2]['open'] < candles[index + 2]['close'] else 'r' if candles[index + 2]['open'] > candles[index + 2]['close'] else 'd'
                        except:
                            mg2_res = False

                        if mg1_res == cor_operacao and mg1_res != False:
                            mg1 += 1

                        elif mg2_res == cor_operacao and mg2_res != False:
                            mg2 += 1

                        else:
                            loss += 1
                            if mg1_res != False: loss +=1
                            if mg2_res != False: loss +=1


                else:
                    doji += 1

        print('\n\n------------Resultado-----------\n\n')
        print(' Win Mao Fixa: ', win)
        print(' Martingale 1: ', mg1)
        print(' Martingale 2: ', mg2)
        print(' Loss: ', loss)
        print(' Entradas Não realizadas: ', doji)
        print(' Winrate: ', round(100*((win + mg1 + mg2) / (win + mg1 + mg2 + loss))))
        print(' Total de Operações: \n\n',  win + mg1 + mg2 + loss)



except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")