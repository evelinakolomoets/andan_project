#!/usr/bin/env python
# coding: utf-8

# ### Импорт необходимых библиотек

# In[1]:


import requests  

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import pandas as pd
import numpy as np

import tempfile, os, zipfile, io

from datetime import date, timedelta

import urllib


# Решение для создания списка дат для итерирования взято с [Stackoverflow](https://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python).

# In[2]:


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


# In[3]:


def categorise_ru_cpi(r, dframe): 
    month = int(r['date_split'][1])
    year = int(r['date_split'][2])
    return dframe.loc[month, year]


# ### Класс для сбора данных

# In[4]:


class FinancialInfo:
    def __init__(self, start_date=None, end_date=None):
        ''' 
        start_date: Первый день, за который надо получить данные. Формат ввода: ДД.ММ.ГГГГ. По умолчанию: 01.01.2010
        end_date: Последний день, за который надо получить данные. Формат ввода: ДД.ММ.ГГГГ. По умолчанию: вчера
        '''
        # задание дефолтного значения первого дня
        if start_date is None:
            self.start_date = date(2010, 1, 1)
            self.start_date_text = self.start_date.strftime("%d.%m.%Y")
        # задание пользовательского значения первого дня
        else:
            self.start_date_text = start_date
            sd = list(map(int, start_date.split('.')))
            self.start_date = date(sd[2], sd[1], sd[0])
            
        # задание дефолтного значения последнего дня
        if end_date is None:
            self.end_date = date.today()
            self.end_date_text = self.end_date.strftime("%d.%m.%Y")
        # задание пользовательского значения последнего дня
        else:
            self.end_date_text = end_date
            ed = list(map(int, end_date.split('.')))
            self.end_date = date(ed[2], ed[1], ed[0])
    
    def get_usdrub(self):
        '''
        Выгружает данные по курсу USDRUB из XML Банка России за даты, указанные в атрибутах объекта.
        '''
        usd = dict()
        
        # в XML Банка России даты заданы в формате ДД/ММ/ГГГГ, поэтому переводим атрибуты в нужный формат
        st_usd = self.start_date.strftime("%d/%m/%Y")
        ed_usd = self.end_date.strftime("%d/%m/%Y")
        
        url_i = f'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={st_usd}&date_req2={ed_usd}&VAL_NM_RQ=R01235'
        response_i = requests.get(url_i, headers={'User-Agent': UserAgent().chrome}, timeout=5)
        tree_usd = BeautifulSoup(response_i.content, 'html.parser')
        
        # в XML все записи внесены как record с датой и значением курса 
        for i in tree_usd.find_all('record'):
            usd[i.get('date')] = float(i.value.text.replace(',', '.'))
        
        usdrub = pd.DataFrame.from_dict(usd, orient='index', columns=['usdrub'])
        
        usdrub.index = pd.to_datetime(usdrub.index, format='%d.%m.%Y')
        
        usdrub = usdrub.resample('1D').mean()
        usdrub = usdrub.sort_index()
        
        usdrub.index = usdrub.index.strftime('%d.%m.%Y')
            
        return usdrub
        
    def get_cb_key_rate(self):
        '''
        Выгружает данные по ключевой ставке с сайта Банка России за даты, указанные в атрибутах объекта.
        '''

        key_policy_rate = dict()
        
        # на сайте ЦБ данные доступны с 17.09.2013. Чтобы избежать риск того, что в ближайшее время 
        # эту дату поменяют, выгружаем данные до 2014 года с другого сайта
        
        threshold = date(2014, 1, 1)
        if self.start_date < date(2014, 1, 1):
            url_additional = 'https://www.audit-it.ru/inform/peni/stavka_cb.php'
            additional = pd.read_html(url_additional)[0]
            additional = additional.drop('Документ, в котором сообщена ставка', axis=1)
            additional['Срок, с которого установлена ставка'] = pd.to_datetime(
                                                    additional['Срок, с которого установлена ставка'], format='%d.%m.%Y')

            additional = additional.set_index('Срок, с которого установлена ставка')
            
            additional.index.names = [None]

            # на этом сайте публикуются только даты изменения ключевой ставки, поэтому заполним пропущенные даты
            additional = additional.resample('1D').mean().ffill()

            additional.index = additional.index.strftime('%d.%m.%Y')
            
            additional.rename({"Размер ставки рефинансирования (%, годовых)": "cb_key_rate"}, 
                              axis=1, inplace=True)
            
        url_k = f'https://www.cbr.ru/hd_base/KeyRate/?UniDbQuery.Posted=True&UniDbQuery.From={threshold.strftime("%d.%m.%Y")}&UniDbQuery.To={self.end_date_text}'
        response_k = requests.get(url_k, headers={'User-Agent': UserAgent().chrome}, timeout=5)
        tree_key_policy_rate = BeautifulSoup(response_k.content, 'html.parser')
        
        key_rate = pd.read_html(str(tree_key_policy_rate.find('div', {'class': "table-wrapper"}).table), index_col='Дата')[0]
        key_rate.index.name = None
        
        # преобразования для сортировки по возрастанию по дате
        key_rate.index = pd.to_datetime(key_rate.index, format='%d.%m.%Y')
        key_rate = key_rate.sort_index()
        key_rate.index = key_rate.index.strftime('%d.%m.%Y')
        
        key_rate['Ставка'] = key_rate['Ставка']/100
        key_rate.rename({'Ставка': 'cb_key_rate'}, axis=1, inplace=True)
        
        return pd.concat([additional[self.start_date_text:threshold.strftime("%d.%m.%Y")], key_rate])
    
    def get_fed_rate(self):
        '''
        Выгружает данные о учетной ставке с сайта ФРС за даты, указанные в атрибутах объекта.
        '''
        
        fed_rate = dict()

        url_fed = 'https://www.federalreserve.gov/datadownload/Output.aspx?rel=PRATES&filetype=zip'
        response_fed = requests.get(url_fed, headers={'User-Agent': UserAgent().chrome})

        # концепт распаковки взят с stackoverflow, но ссылка потерялась
        with response_fed, zipfile.ZipFile(io.BytesIO(response_fed.content)) as archive:
            data = archive.read('PRATES_data.xml')

        all_fed_data = BeautifulSoup(str(data), 'lxml').find(id='PRATES_POLICY_RATES').find_all('frb:obs')

        for m in all_fed_data:
            date_lst = list(map(int, m.get('time_period').split('-')))
            date_dt = date(date_lst[0], date_lst[1], date_lst[2])
            if date_dt >= self.start_date and date_dt <= self.end_date:
                fed_rate[date_dt.strftime("%d.%m.%Y")] = float(m.get('obs_value'))
                
        return pd.DataFrame.from_dict(fed_rate, orient='index', columns=['fed_rate'])
        
    def get_gold(self):
        '''
        Выгружает данные по цене золота из XML Банка России за даты, указанные в атрибутах объекта.
        '''
        
        gold_buy = dict()
        url_gold = f'http://www.cbr.ru/scripts/xml_metall.asp?date_req1={self.start_date_text}&date_req2={self.end_date_text}'
        response_gold = requests.get(url_gold, headers={'User-Agent': UserAgent().chrome})
        tree_gold = BeautifulSoup(response_gold.content, 'html.parser')
        for j in tree_gold.metall.find_all('record', code='1'):
            j_date = j.get('date')
            gold_buy[j_date] = float(j.buy.text.replace(',', '.'))
            
        return pd.DataFrame.from_dict(gold_buy, orient='index', columns=['gold'])
    
    def get_imoex(self):
        '''
        Выгружает данные по ценам открытия и закрытия Индекса Мосбиржи из ISS Московской Биржи за даты, указанные в атрибутах объекта.
        '''
        imoex = dict()

        st_imoex = self.start_date.strftime("%Y-%m-%d")
        ed_imoex = self.end_date.strftime("%Y-%m-%d")

        # этот кусок нужен, потому что система по запросу выдает только 100 дат. В инструкции к ISS
        # Московской биржи есть более элегантное решение этой проблемы, но по неведомым нам причинам
        # оно не работает. Поэтому боремся, как можем
        
        url_im = f'https://iss.moex.com/iss/history/engines/stock/markets/index/sessions/SNDX/securities/IMOEX.xml?from={st_imoex}&till={ed_imoex}'
        response_im = requests.get(url_im, headers={'User-Agent': UserAgent().chrome}, timeout=5)
        tree_im = BeautifulSoup(response_im.content, 'lxml')

        imoex_urls = []

        total_days = np.arange(100, (self.end_date - self.start_date).days+100, 100)

        for start, end in zip(np.arange(0, (self.end_date - self.start_date).days, 100), total_days):
            url_start = (self.start_date+timedelta(days=int(start))).strftime("%Y-%m-%d")
            url_end = (self.start_date+timedelta(days=int(end))).strftime("%Y-%m-%d")
            imoex_urls.append(f'https://iss.moex.com/iss/history/engines/stock/markets/index/sessions/SNDX/securities/IMOEX.xml?from={url_start}&till={url_end}')


        for url_im in imoex_urls:
            response_im = requests.get(url_im, headers={'User-Agent': UserAgent().chrome}, timeout=5)
            tree_im = BeautifulSoup(response_im.content, 'lxml')

            # до -1 элемента, потому что также есть row со значениями 
            # index, total и start, т.е. служебная строка
            for moex_value in tree_im.find_all('row')[:-1]: 
                # переводим дату из исходного формата tradedate="YYYY-MM-DD" в формат "DD.MM.YYYY"
                moex_date = '.'.join(moex_value.get('tradedate').split('-')[::-1]) 
                # записываем цены открытия и закрытия индекса на дату в словарь словарей
                imoex[moex_date] = dict()
                imoex[moex_date]['imoex_open'] = float(moex_value.get('open'))
                imoex[moex_date]['imoex_close'] = float(moex_value.get('close'))
                
        return pd.DataFrame.from_dict(imoex, orient='index', columns=['imoex_open', 'imoex_close'])
    
    def get_ru_cpi(self):
        '''
        Выгружает данные по значению Индекса Потребительских цен (ИПЦ) в России с сайта Росстата за даты, указанные в атрибутах объекта.
        '''
        url_ru_cpi = 'https://rosstat.gov.ru/storage/mediabank/Ipc_mes-3.xlsx'

        file_ru_cpi = urllib.request.urlopen(url_ru_cpi).read()

        all_ru_cpi = pd.read_excel(file_ru_cpi, sheet_name='01', skiprows=3, header=0, nrows=13)

        # строка "к концу предыдущего месяца" не нужна
        all_ru_cpi.drop(0, inplace=True) 

        # строка с названиями месяцев в исходном файле не подписана, подпишем её
        all_ru_cpi.rename({'Unnamed: 0': 'месяц'}, axis='columns', inplace=True) 
        years_needed = all_ru_cpi.loc[:, self.start_date.year:self.end_date.year]

        ru_cpi = pd.DataFrame()
        ru_cpi['date'] = [i.strftime("%d.%m.%Y") for i in daterange(self.start_date, self.end_date)]
        ru_cpi['date_split'] = ru_cpi['date'].str.split('.')
        ru_cpi['ru_cpi'] = ru_cpi.apply(lambda row: categorise_ru_cpi(row, years_needed), axis=1)
        ru_cpi.drop('date_split', axis=1, inplace=True)
        ru_cpi = ru_cpi.set_index('date')
        ru_cpi.index.names = [None]
        return ru_cpi
    
    def get_us_cpi(self):
        '''
        Выгружает данные по значению Индекса Потребительских цен (ИПЦ) в США с сайта ФРБ St.Louis за даты, указанные в атрибутах объекта.
        '''
        # к сожалению, организация, официально публикующая инфляцию в США, U.S. Bureau of Labor Statistics, 
        # судя по всему, банит российские ip-адреса

        # в найденном источнике 1982-1984 принято за 100, что бы это ни значило
        all_us_cpi = pd.read_csv('https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1138&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CPIAUCSL&scale=left&cosd=1947-01-01&coed=2023-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2023-05-01&revision_date=2023-05-01&nd=1947-01-01')

        # чтобы вывести ИПЦ месяц-к-месяцу, зная ИПЦ к базовому периду, нужно ИПЦ t+1 периода поделить 
        # на ИПЦ t периода и умножить на 100, это следует из формулы: сумма по корзине (P_t*Q_0)/(P_0*Q_0) * 100

        # чтобы поделить было проще, создадим дополнительную колонку, где все значения будут сдвинуты
        # на одну позицию вниз
        all_us_cpi['CPIAUCSL_shift'] = np.roll(all_us_cpi['CPIAUCSL'], 1)
        all_us_cpi['us_cpi'] = all_us_cpi['CPIAUCSL_shift']/all_us_cpi['CPIAUCSL'] * 100

        # обработка данных о дате
        all_us_cpi['DATE'] = pd.to_datetime(all_us_cpi['DATE'], format='%Y-%m-%d')

        all_us_cpi = all_us_cpi.set_index('DATE')
        all_us_cpi.index.names = [None]
        
        # заполняем пропущенные дни, т.к. данные на 1 число каждого месяца
        # пропуски на весь месяц заполним ИПЦ на 1 число этого же месяца
        all_us_cpi = all_us_cpi.resample('1D').mean().ffill()
        all_us_cpi.index = all_us_cpi.index.strftime('%d.%m.%Y')
        all_us_cpi.drop(['CPIAUCSL', 'CPIAUCSL_shift'], axis=1, inplace=True)

        return all_us_cpi[self.start_date_text:]
    
    def get_holidays(self):
        '''Выгружает выходные и праздничные дни в соответствии с производственным календарем за даты, указанные в атрибутах объекта'''
        all_holidays = dict()

        years = np.arange(self.start_date.year, self.end_date.year+1)

        months = np.arange(12)

        for y in years:
            calendar_url = f'https://calendar.yoip.ru/work/{y}-proizvodstvennyj-calendar.html'
            cal = requests.get(calendar_url, headers={'User-Agent': UserAgent().chrome}, timeout=5)
            tree_cal = BeautifulSoup(cal.content, 'html.parser')
            for m in months:
                netraboty_m = [int(i.text) for i 
                             in tree_cal.find_all('table')[m].find_all('td', {'class': '_hd danger tt-hd'})]
                netraboty_m.extend([int(i.text) for i 
                                  in tree_cal.find_all('table')[m].find_all('td', {'class': '_hd warning tt-hd'})])
                netraboty_m.extend([int(i.text) for i 
                                 in tree_cal.find_all('table')[m].find_all('td', {'class': '_hd warning'})])
                netraboty_m = [date(y, m+1, i) for i in sorted(netraboty_m)]
                for day in netraboty_m:
                    all_holidays[day.strftime("%d.%m.%Y")] = 'day off'
        
        calendar_df = pd.DataFrame.from_dict(all_holidays, orient='index', columns=['workday'])
        return calendar_df

    def get_all(self):
        '''
        Выгружает данные по цене золота, курсу USDRUB, ключевой ставке Банка России, ценам открытия и закрытия Индекса Мосбиржи, ИПЦ в РФ за даты, указанные в атрибутах объекта.
        '''
        df = pd.merge(self.get_usdrub(),self.get_gold(),  
                                how='left', left_index=True, right_index=True)
        df = pd.merge(df, self.get_cb_key_rate(), 
                        how='left', left_index=True, right_index=True)
        df = pd.merge(df, self.get_fed_rate(), 
                             how='left', left_index=True, right_index=True)
        df = pd.merge(df, self.get_imoex(), 
                        how='left', left_index=True, right_index=True)
        df = pd.merge(df, self.get_ru_cpi(), how='left', left_index=True, right_index=True)
        
        df = pd.merge(df, self.get_us_cpi(), how='left', left_index=True, right_index=True)
        
        df.index = pd.to_datetime(df.index, format='%d.%m.%Y')
        df = df.sort_index()
        df.index = df.index.strftime('%d.%m.%Y')
        df = pd.merge(df, self.get_holidays(), how='left', left_index=True, right_index=True)
        
        df['workday'] = df['workday'].fillna('workday')
        
        return df

