from selenium import webdriver
import datetime as dt
import pandas as pd
import os


class FocusIPCA(object):
    """
    Classe para puxar os dados de IPCA do focus.
    - Selenium Webdriver
    """

    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()

    def scrape(self, initial_date, end_date):

        # Chrome WebDriver is created
        browser = webdriver.Chrome()

        # navigating to the page
        browser.get("https://www3.bcb.gov.br/expectativas/publico/consulta/serieestatisticas")

        # select the indicator
        xpath = r'//*[@id="indicador"]/option[5]'
        browser.find_element_by_xpath(xpath).click()

        # select the price index
        xpath = r'// *[ @ id = "grupoIndicePreco:opcoes_6"]'
        browser.find_element_by_xpath(xpath).click()

        # select the metric - median
        xpath = r'//*[@id="calculo"]/option[3]'
        browser.find_element_by_xpath(xpath).click()

        # select the periodicity - monthly
        xpath = r'//*[@id="periodicidade"]/option[2]'
        browser.find_element_by_xpath(xpath).click()

        # dates in string format
        if type(initial_date) is str:
            initial_date = pd.to_datetime(initial_date).strftime('%m/%d/%Y')
        else:
            initial_date = initial_date.strftime('%m/%d/%Y')

        # dates in string format
        if type(end_date) is str:
            end_date = pd.to_datetime(end_date).strftime('%m/%d/%Y')
        else:
            end_date = end_date.strftime('%m/%d/%Y')

        # there is a limit of two years to grab the data
        while end_date.year - initial_date.year >= 2:
            initial_date = pd.to_datetime(initial_date)
            end_date = pd.to_datetime(end_date)

            aux_end_date = dt.date(initial_date.day, initial_date.month, initial_date.year + 2)

            'same as above'

            df = pd.read_excel(file_path, skiprows=1, na_values=[' '])

            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            df = df.set_index('Data')

            list_df = list_df.append(df)

            initial_date.year = initial_date.year + 2


        # fill the dates
        xpath = r'//*[@id="tfDataInicial7"]'
        browser.find_element_by_xpath(xpath).send_keys(initial_date)

        # fill the dates
        xpath = r'//*[@id="tfDataFinal8"]'
        browser.find_element_by_xpath(xpath).send_keys(end_date)

        # fill initial month
        initial_month = pd.to_datetime(initial_date).month
        xpath = r'//*[@id="mesReferenciaInicial"]/option[{}]'.format(initial_month)
        browser.find_element_by_xpath(xpath).click()

        # fill initial year
        initial_year = pd.to_datetime(initial_date).year
        xpath = r'//*[@id="form7"]/div[2]/table/tbody[3]/tr/td[2]/select[2]/option[{}]'.format(initial_year)
        browser.find_element_by_xpath(xpath).click()

        # fill final month
        end_month = pd.to_datetime(initial_date).month
        xpath = r'//*[@id="mesReferenciaFinal"]/option[{}]'.format(end_month)
        browser.find_element_by_xpath(xpath).click()

        # fill final year
        end_year = pd.to_datetime(initial_date).year
        xpath = r'//*[@id="form7"]/div[2]/table/tbody[3]/tr/td[4]/select[2]/option[{}]'.format(end_year)
        browser.find_element_by_xpath(xpath).click()

        # click the download button
        xpath = r'//*[@id="btnXLSd"]'
        browser.find_element_by_xpath(xpath).click()

        # saves the time the file was downloaded
        download_save_time = dt.datetime.now()

        # get the default download directory
        username = os.getlogin()
        download_path = r'C:\Users\%(user)s\Downloads' % {'user': username}

        for (dirpath, dirnames, filenames) in os.walk(download_path):
            for f in filenames:
                if 'Séries de estatísticas' in f:
                    file_save_time = os.path.getmtime(dirpath + '\\' + f)
                    file_save_time = dt.datetime.fromtimestamp(file_save_time)

                    if file_save_time > download_save_time:
                        file_path = dirpath + '\\' + f

        # read the file and clean the dataframe
        df = pd.read_excel(file_path, skiprows=1, na_values=[' '])

        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
        df = df.set_index('Data')
        pass
