import configparser
import getpass
import json
import sys

from iqoptionapi.iqoptionapi.stable_api import IQ_Option
import Fernet as Fernet
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
    return {'lo': arquivo.get('login', 'u').replace('\'','"'), 's': arquivo.get('login', 's').replace('\'','"'), 'entrada': arquivo.get('parametros', 'valor_entrada'), 'mg': arquivo.get('parametros', 'qtd_mg'), 'loss': arquivo.get('parametros', 'stop_loss'), 'gain': arquivo.get('parametros', 'stop_gain'), 'modo': arquivo.get('parametros', 'modo_conta'), 'delay': arquivo.get('parametros', 'delay'), 'payout': arquivo.get('parametros', 'payout_min'), 'soros': arquivo.get('parametros', 'qtd_soros'),}

def payout(par, tp_market, timeframe_in_min):
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

def best_payout(par, timeframe):
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

def verifica_stops(lucro_total, stop_loss):
    if lucro_total >= stop_gain:
        print('\nEscapou hj. So alegria. Stop Gain atingido com Muito Sucesso!! De uma fuga. Amanha tem mais.\n')
        print(50 * '-')
        sys.exit()
    elif lucro_total <= -stop_loss:
        print(
            '\nStop Loss Atingido, mas acontece. Amanha tem mais! Amanha.\n')
        print(50 * '-')
        sys.exit()

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

    payoutMin = int(config['payout'])

    delay = float(config['delay'])

    qtd_gale = int(config['mg'])
    qtd_soros = int(config['mg'])
    stop_gain = float(config['gain'])
    stop_loss = float(config['loss'])
    valorIni = float(config['entrada'])
    valorIniAux = valorIni

    arquivo = input('Arquivo com sinais: ') # Arquivo.txtparame
    arquivo = open(arquivo, 'r').read()
    arquivo = arquivo.split('\n')

    isBusinQuad = True if(input('Deseja executar gerenciamento quadratico? y=sim n=não') == 'y') else False

    print('\n\n')

    cont_win = 0
    cont_loos = 0
    lucro_total = 0


    for dados in sorted(arquivo):

        if dados.strip() != '':
            dados = dados.split(',')

            horario = datetime.strptime(dados[0], '%Y-%m-%d %H:%M:%S')
            horario = datetime.timestamp(horario)
            par = dados[1]
            dir = dados[2]
            timeframe = dados[3]

            tpMercado = best_payout(par, timeframe)

            print('\n Aguardando entrada...\n')

            while(True):
                if float(datetime.now()) <= float(horario) -delay:

                    if float(datetime.now()) == float(horario) -delay: # Ver formato do horario se o delay é -3 ou -0,2 -0,1 .... se é float ou int

                        atualPayout = payout(par, tpMercado, timeframe)

                        if atualPayout >= payoutMin:

                            if tpMercado == 'digital':

                                statusCompra, id = Iq.buy_digital_spot(par, valorIni, dir, timeframe)

                                if statusCompra:
                                    while True:
                                        status, lucro = Iq.check_win_digital_v2(id)
                                        if status:
                                            if isBusinQuad:
                                                if lucro >= 0:
                                                    print('GAINN | Lucro ' + lucro)
                                                    cont_win += 1
                                                    cont_loos = 0
                                                    if cont_win < qtd_soros:
                                                        valorIni += lucro
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                                else:
                                                    cont_loos += 1
                                                    cont_win = 0
                                                    print('LOOS | - ' + valorIni)
                                                    valorIni = auto_martingale('', valorIniAux, atualPayout, valorIni)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                            else:
                                                if lucro >= 0:
                                                    cont_win += 1
                                                    cont_loos = 0
                                                    valorIni = valorIniAux
                                                    print('GAINN | Lucro '+lucro)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break

                                                else:
                                                    cont_loos += 1
                                                    cont_win = 0
                                                    print('LOOS | - ' + valorIni)
                                                    valorIni = auto_martingale('', valorIniAux, atualPayout, valorIni)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                else:
                                    print('Erro na Compra!')
                                    break
                            else:

                                statusCompra, id = Iq.buy(valorIni, par, dir, timeframe)

                                if statusCompra:
                                    while True:
                                        status, lucro = Iq.check_win_v4(id)
                                        if status:
                                            if isBusinQuad:
                                                if lucro >= 0:
                                                    print('GAINN | Lucro ' + lucro)
                                                    cont_win += 1
                                                    cont_loos = 0
                                                    if cont_win < qtd_soros:
                                                        valorIni += lucro
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                                else:
                                                    cont_loos += 1
                                                    cont_win = 0
                                                    print('LOOS | - ' + valorIni)
                                                    valorIni = auto_martingale('', valorIniAux, atualPayout, valorIni)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                            else:
                                                if lucro >= 0:
                                                    cont_win += 1
                                                    cont_loos = 0
                                                    valorIni = valorIniAux
                                                    print('GAINN | Lucro ' + lucro)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break

                                                else:
                                                    cont_loos += 1
                                                    cont_win = 0
                                                    print('LOOS | - ' + valorIni)
                                                    valorIni = auto_martingale('', valorIniAux, atualPayout, valorIni)
                                                    lucro_total += lucro
                                                    verifica_stops(lucro_total, stop_loss)
                                                    break
                                else:
                                    print('Erro na Compra!')
                                    break
                else:
                    break
            # velas = Iq.get_candles(dados[1].upper(), (timeframe * 60), 1, int(horario))
            #
            # if int(velas[0]['from']) == int(horario):
            #     dir = 'call' if velas[0]['open'] < velas[0]['close'] else 'put' if velas[0]['open'] > velas[0]['close'] else 'doji'
            #
            #     if dir == dados[2].lower():
            #         print(dados[0], dados[1], dados[2], '|', Fore.GREEN + 'WIN')
            #         win +=1
            #     else:
            #         print(dados[0], dados[1], dados[2], '|', Fore.RED + 'LOOS')
            #         loos += 1
            # else:
            #     print(dados[0], dados[1], dados[2], '|', Fore.RED + 'Não foi possível carregar dados desta vela!')



except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")