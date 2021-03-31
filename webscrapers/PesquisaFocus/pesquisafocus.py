from selenium import webdriver
import datetime as dt
import pandas as pd
import os
import time as time


class FocusIPCA(object):
    """
    Classe para puxar os dados de IPCA do focus.
    - Selenium Webdriver
    """

    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()

    def scrape(self, initial_date, end_date):
        browser = webdriver.Chrome("C:/Users/mathe/Downloads/chromedriver_win32/chromedriver.exe",
                                   chrome_options=self.driver_options)

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

        # dates in datetime format
        initial_date = pd.to_datetime(initial_date, format='%d/%m/%Y')
        end_date = pd.to_datetime(end_date, format='%d/%m/%Y')

        aux_initial_date = initial_date  # to grab the data each 2 year
        list_df = []  # to concat all the df at the end
        stop_grab = False  # to stop the while
        while True:
            if end_date.year - initial_date.year >= 2:
                aux_end_date = aux_initial_date + dt.timedelta(days=729)  # adjust the end date
                more_than_2years = 1  # identify if the range is more than 2 years

                # it means the time range is less than two years after some loops
                # that's why we adjust the aux_end_date to grab the rest of the data between initial_date and end_date
                if aux_end_date >= end_date:
                    aux_end_date = end_date  # adjust the end date
                    stop_grab = True  # final loop
            else:
                more_than_2years = 0  # identify if the range is less than 2 years
                aux_end_date = end_date

            # fill the dates
            xpath = r'//*[@id="tfDataInicial1"]'
            browser.find_element_by_xpath(xpath).send_keys(aux_initial_date.strftime('%d/%m/%Y'))

            # fill the dates
            xpath = r'//*[@id="tfDataFinal2"]'
            browser.find_element_by_xpath(xpath).send_keys(aux_end_date.strftime('%d/%m/%Y'))

            # fill initial month
            xpath = r'//*[@id="mesReferenciaInicial"]/option[{a}]'.format(a=aux_initial_date.month + 1)
            browser.find_element_by_xpath(xpath).click()

            # fill initial year
            xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[2]/select[2]/option[{a}]'.format(a=aux_initial_date.year - 1997)
            browser.find_element_by_xpath(xpath).click()

            # fill final month
            xpath = r'//*[@id="mesReferenciaFinal"]/option[{a}]'.format(a=aux_end_date.month + 1)
            browser.find_element_by_xpath(xpath).click()

            # fill final year
            xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[4]/select[2]/option[{a}]'.format(
                a=aux_end_date.year - 1997)
            browser.find_element_by_xpath(xpath).click()

            # click the download button
            xpath = r'//*[@id="btnXLSa"]'
            browser.find_element_by_xpath(xpath).click()

            # saves the time the file was downloaded
            download_save_time = dt.datetime.now()

            # clear initial date and end date fo the next loop
            xpath = r'//*[@id="tfDataInicial1"]'
            browser.find_element_by_xpath(xpath).clear()
            xpath = r'//*[@id="tfDataFinal2"]'
            browser.find_element_by_xpath(xpath).clear()

            # give some time for the download to finish
            time.sleep(6)

            # get the default download directory
            username = os.getlogin()
            download_path = r'C:/Users/{}/Downloads'.format(username)

            for (dirpath, dirnames, filenames) in os.walk(download_path):

                for f in filenames:

                    if 'Séries de estatísticas' in f:
                        file_save_time = os.path.getmtime(dirpath + '\\' + f)
                        file_save_time = dt.datetime.fromtimestamp(file_save_time)

                        if file_save_time > download_save_time:
                            file_path = dirpath + '\\' + f

            # read the file and clean the dataframe
            df = pd.read_excel(file_path, skiprows=1, na_values=[' '])

            # data to datetime and setting data as index
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            df = df.set_index('Data')

            if more_than_2years == 1:
                list_df.append(df)  # df's that will be concatenated
                aux_initial_date = aux_end_date + dt.timedelta(days=1)  # adjust the initial date

                if stop_grab:
                    df = pd.concat(list_df)  # concatenate all the data grabbed
                    break
            else:
                break

        browser.close()

        return df
