import sys

from iqoptionapi.stable_api import IQ_Option
import logging
from datetime import datetime, timedelta
from colorama import init, Fore, Back
from time import time
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

init(autoreset=True)

# pip install selenium
# https://www.selenium.dev/documentation/en/webdriver/driver_requirements/
# pip install bs4
# https://iqoption.com/en/trading-hours-and-fees?tab=options



logging.disable(level=(logging.DEBUG))

def set_config():
    try:
        binary = FirefoxBinary("Caminho no pc")##
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')#modo silencioso (Sem abrir o navegador)
        browser = webdriver.Firefox(firefox_binary=binary, options=options)

        return True, browser

    except:
        return False, None

def get_data(browser):
    xpath = {
        'Show More': '/html/body/div[5]/div/div[2]/div[2]/div[2]/div[2]/div/div/button',
        'change type': '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/div[1]',
        'Binary Options': '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/div[2]/div/div/div[1]',
        'Digital Options': '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/div[2]/div/div/div[2]'
    }

    browser.get("https://iqoption.com/en/trading-hours-and-fees?tab=options")
    webdriverWait(browser, 10).util(EC.element_to_be_clickable((By.xpath['Show More'])))

    sources = {'Digital': '', 'Binary': ''}

    for type in sources:
        browser.find_element_by_xpath(xpath['change type']).click()
        browser.find_element_by_xpath(xpath[type + 'Options']).click()

        for i in range(3):
            try:
                browser.find_element_by_xpath(xpath['Show More']).click()
                sleep(0.5)
            except:
                pass
        sources[type] = browser.page_source

    browser.close()

    return sources

def parse(html):
    resultados = {}
    dias = {'Sun': 'Domingo', 'Mon': 'Segunda', 'Tue': 'Terça', 'Wed': 'Quarta', 'Thu': 'Quinta', 'Fri': 'Sexta', 'Sat': 'Sabado'}

    info = BeautifulSoup(html, 'html.parser')
    blocos = ((info.find('table', {'class': 'FeesTable'})).find('tbody')).findAll('tr', {'class': 'FeesTableBody__rowAsset'})

    for blocos2 in blocos:
        par = blocos2.find('td', {'class': 'tableCell_instrument'}).contents[0].contents[1].contents[1].string
        horarios = blocos2.finAll('div', {'class': 'FeeAssetSchedule__item'})

        listaHorarios = []

        for horario in horarios:
            dia = horario.find('div', {'class', 'FeeAssetSchedule__itemDay'}).string
            hora = horario.find('div', {'class', 'FeeAssetSchedule__itemTime'}).string

            if '-' in dia:
                d = dia.split(' - ')

                dia = [dias[ d[i] ] for i in range(2) if d[i] in dias]
                # for i in range(2):
                #     if d[i] in dias : d[i] = dias[d[i]]

                dia = dia[0] + ' - ' + dia[1]
            elif dia in dias:
                dia = dias[dia]

            listaHorarios.append({'dia': dia, 'hora': hora})

        if len(listaHorarios) != 0 and par not in resultados : resultados.update({par: listaHorarios})

    return resultados




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

    print('--Iniciando captura de horarios e pares, \nSetando Configurações...\n')

    sta, conf = set_config()

    dados = {'Digital': '', 'Binary': ''}

    if sta == True:
        print('*Iniciando captura de dados!')
        source = get_data(conf)

        if len(source['Digital'])>0:
            print('Iniciando tratamento dos dados...')

            for save in dados:
                dados[save] = parse(source[save])

    if len(dados['Digital'])==0 and len(dados['Binary'])==0:
        print('[!] Não foi possivel carregar dados!')

    else:
        for tipo in dados:
            print('\n\n{ ',tipo,' ]')
            for par in dados[tipo]:
                print('Paridade: ', par)

                for dia_hora in dados[tipo][par]:
                    print('Dia: ', dia_hora['dia'], ' / HORA: ', dia_hora['hora'])

                print(50*'-')



except ValueError as ve:
    print(ve)
    print("Parando o Bot")

except KeyboardInterrupt:
    print("Parando o Bot")