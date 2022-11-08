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

    print('\n\nQual timeframe deseja catalogar? ', end='')
    timeframe = int(input())
    #
    # print('\nQuantos dias deseja analizar? ', end='')
    # dias = int(input())
    #
    # print('\nQual a porcentagem minima? ', end='')
    # porcentagem = int(input())
    #
    # print('\nTestar com quantos martingales? ', end='')
    # qtd_martingales = int(input())

    arquivo = input('Arquivo com sinais: ') # Arquivo.txt
    arquivo = open(arquivo, 'r').read()
    arquivo = arquivo.split('\n')

    print('\n\n')

    win = 0
    loos = 0


    for dados in sorted(arquivo):

        if dados.strip() != '':
            dados = dados.split(',')

            horario = datetime.strptime(dados[0], '%Y-%m-%d %H:%M:%S')
            horario = datetime.timestamp(horario)

            velas = Iq.get_candles(dados[1].upper(), (timeframe * 60), 1, int(horario))

            if int(velas[0]['from']) == int(horario):
                dir = 'call' if velas[0]['open'] < velas[0]['close'] else 'put' if velas[0]['open'] > velas[0]['close'] else 'doji'

                if dir == dados[2].lower():
                    print(dados[0], dados[1], dados[2], '|', Fore.GREEN + 'WIN')
                    win +=1
                else:
                    print(dados[0], dados[1], dados[2], '|', Fore.RED + 'LOOS')
                    loos += 1
            else:
                print(dados[0], dados[1], dados[2], '|', Fore.RED + 'Não foi possível carregar dados desta vela!')


    print(50 * '-')

    print(' [ Resultados ] ')
    print('WINS: ' + Fore.GREEN + str(win))
    print('LOOS: ' + Fore.RED + str(loos))
    print('WINRATE: ' + str(round((win / (win+loos)) * 100)))

    input('Aperte ENTER para fechar o programa')



except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")