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

    print('\nQuantos dias deseja analizar? ', end='')
    dias = int(input())

    print('\nQual a porcentagem minima? ', end='')
    porcentagem = int(input())

    print('\nTestar com quantos martingales? ', end='')
    qtd_martingales = int(input())

    prct_call = abs(porcentagem)
    prct_put = abs(100 - porcentagem)

    p = Iq.get_all_open_time()

    print('\n\n')

    catalogacao = {}

    for par in p['digital']:
        if p['digital'][par]['open'] == True:
            timer = int(time())

            print(Fore.GREEN + '*' + Fore.RESET + ' CATALOGANDO ' + par + '..', end='')

            catalogacao.update({par: cataloga(par, dias, prct_call, prct_put, timeframe)})

            if qtd_martingales.strip() != '':
                for horario in sorted(catalogacao[par]):
                    mg_time = horario

                    soma = {'verde': catalogacao[par][horario]['verde'], 'vermelha': catalogacao[par][horario]['vermelha'], 'doji': catalogacao[par][horario]['doji']}

                    for i in range(int(qtd_martingales)):
                        catalogacao[par][horario].update({'mg'+str(i+1): {'verde': 0, 'vermelha': 0, 'doji': 0, '%': 0}})

                        mg_time = str(datetime.strptime((datetime.now()).strftime('%Y-%m-%d ') + mg_time, '%Y-%m-%d %H:%M') + timedelta(minutes=timeframe))[11:-3]

                        if mg_time in catalogacao[par]:
                            catalogacao[par][horario]['mg' + str(i+1)]['verde'] += catalogacao[par][mg_time]['verde'] + soma['verde']
                            catalogacao[par][horario]['mg' + str(i+1)]['vermelha'] += catalogacao[par][mg_time]['verde'] + soma['vermelha']
                            catalogacao[par][horario]['mg' + str(i+1)]['doji'] += catalogacao[par][mg_time]['verde'] + soma['doji']

                            catalogacao[par][horario]['mg' + str(i)]['%'] = round(100 * (catalogacao[par][horario]['mg' + str(i)]['verde' if catalogacao[par][horario]['dir'] =='CALl' else 'vermelha'] / (catalogacao[par][horario]['mg' + str(i)]['verde'] + catalogacao[par][horario]['mg' + str(i)]['vermelha'] + catalogacao[par][horario]['mg' + str(i)]['doji'])))

                            soma['verde'] += catalogacao[par][horario]['mg' + str(i)]['verde']
                            soma['vermelha'] += catalogacao[par][horario]['mg' + str(i)]['vermelha']
                            soma['doji'] += catalogacao[par][horario]['mg' + str(i)]['doji']
                        else:
                            catalogacao[par][horario]['mg' + str(i)]['%'] = 'N/A'

            print('Finalizado em ' + str(int(time())-timer) + ' segundos!')

    print('\n\n')

    for par in catalogacao:
        for horario in sorted(catalogacao[par]):
            ok = False
            msg = ''
            if catalogacao[par][horario]['%'] >= porcentagem:
                ok = True
            else:
                if qtd_martingales.strip() != '':
                    for i in range(int(qtd_martingales)):
                        if catalogacao[par][horario]['mg' + str(i + 1)]['%'] >= porcentagem:
                            ok = True
                            break

            if ok == True:
                msg = Fore.YELLOW + par + Fore.RESET + ' - ' + horario + ' - ' + (Fore.GREEN if catalogacao[par][horario]['dir'] == 'CALL' else Fore.RED) + catalogacao[par][horario]['dir'] + Fore.RESET + ' - ' + str(catalogacao[par][horario]['%']) + '% - ' + Back.GREEN + Fore.BLACK + str(catalogacao[par][horario]['verde']) + Back.RED + str(catalogacao[par][horario]['vermelha']) + Back.RESET + Fore.RESET + str(catalogacao[par][horario]['doji'])

                if qtd_martingales.strip() != '':
                    for i in range(int(qtd_martingales)):
                        i += 1
                        if str(catalogacao[par][horario]['mg' + str(i)]['%']) != 'N/A':
                            msg += '..| MG ' + str(i) + ' - ' + str(catalogacao[par][horario]['mg' + str(i)]['%']) + '% - ' + Back.GREEN + Fore.BLACK + str(catalogacao[par][horario]['mg' + str(i)]['verde']) + Back.RED + str(catalogacao[par][horario]['mg' + str(i)]['vermelha']) + Back.RESET + Fore.RESET + str(catalogacao[par][horario]['mg' + str(i)]['doji'])

                        else:
                            msg +='..| MG ' + str(i) + ' - N/A - N/A'

                print(msg)

                open('sinais_' + (datetime.now()).strftime('%Y-%m-%d') + '_' + str(timeframe) + 'M.txt', 'a').write( (datetime.now()).strftime('%y-%m-%d') + ' ' + horario + ',' + par + ',' + catalogacao[par][horario]['dir'].strip() + '\n')



except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")