from selenium import webdriver
import datetime as dt
import pandas as pd
import os
import time as time
import platform
import getpass


class Focus(object):
    """
    Classe para puxar os dados do PIB total e IPCA do focus.

    """
    indicator_dict = {'ipca': '5', 'pib': '9'}
    metric_dict = {'mean': '2', 'median': '3', 'std': '4', 'vc': '5',
                   'max': '6', 'min': '7'}
    freq_dict = {'monthly': '2', 'quarterly': '2', 'yearly': '3'}

    def __init__(self, driver_path):
        """
        Parameters
        ----------
        driver_path: path of the chromedriver executable
        """
        self.driver_options = webdriver.ChromeOptions()
        self.driver_path = driver_path

    def scrape(self, indicator, initial_date, end_date, metric='median', frequency='yearly'):
        """
        Parameters
        ----------
        indicator: str with the indicator. Possible values are Focus.indicator_dict
        initial_date: must be understandable by pandas.to_datetime
        end_date: must be understandable by pandas.to_datetime
        metric: str with the statistical metric. Possible values are Focus.metric_dict
        frequency: str with the frequency of the forecast. Possible values are Focus.frequncy_dict

        Returns
        -------
        pandas DataFrame with the timeseries of each forecast horizon available.
        """

        # assert that the chosen parameters exists
        assert indicator in self.indicator_dict.keys(), f"the indicator {indicator} is not available"
        assert metric in self.metric_dict.keys(), f"the metric {metric} is not available"
        assert frequency in self.freq_dict.keys(), f"the frequency {frequency} is not available"

        # ckeck if the indicator and frequency match
        if (indicator == 'pib' and metric == 'monthly') or (indicator == 'ipca' and metric == 'quarterly'):
            raise ValueError('Periodicity selected is not available for the indicator chosen.')

        # open the browser
        browser = webdriver.Chrome(self.driver_path, chrome_options=self.driver_options)

        # navigating to the page
        browser.get("https://www3.bcb.gov.br/expectativas/publico/consulta/serieestatisticas")

        # select the indicator - chooses PIB or IPCA
        xpath = f'//*[@id="indicador"]/option[{self.indicator_dict[indicator]}]'
        browser.find_element_by_xpath(xpath).click()

        # select the price index or the gdp group
        if indicator == 'pib':
            xpath = '//*[@id="grupoPib:opcoes_3"]'  # total gdp
            browser.find_element_by_xpath(xpath).click()
        else:
            xpath = r'//*[@id="grupoIndicePreco:opcoes_6"]'  # IPCA
            browser.find_element_by_xpath(xpath).click()

        # select the metric
        xpath = f'//*[@id="calculo"]/option[{self.metric_dict[metric]}]'
        browser.find_element_by_xpath(xpath).click()

        # select the periodicity
        xpath = f'//*[@id="periodicidade"]/option[{self.freq_dict[frequency]}]'
        browser.find_element_by_xpath(xpath).click()

        # dates in datetime format
        initial_date = pd.to_datetime(initial_date)
        end_date = pd.to_datetime(end_date)

        # generate the date_ranges in 18-month intervals (approximatly)
        dates = pd.date_range(initial_date, end_date, freq='18m')
        dates = list(dates)
        dates[0] = initial_date

        # loops on all date pairs
        list_df = []

        for init_d, end_d in zip(dates[:-1], dates[1:]):

            # fill the dates
            xpath = r'//*[@id="tfDataInicial1"]'
            browser.find_element_by_xpath(xpath).send_keys(init_d.strftime('%d/%m/%Y'))
            xpath = r'//*[@id="tfDataFinal2"]'
            browser.find_element_by_xpath(xpath).send_keys(end_d.strftime('%d/%m/%Y'))

            # fill starting prediction scope (always chooses the first element of the dropdown menu)
            if frequency == 'monthly':
                xpath_m = r'//*[@id="mesReferenciaInicial"]/option[text()="janeiro"]'
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[2]/select[2]/option[text()="1999"]'
                browser.find_element_by_xpath(xpath_m).click()
                browser.find_element_by_xpath(xpath).click()

            elif frequency == 'quarterly':
                xpath_m = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[2]/select[1]/option[text()="janeiro a março"]'
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[2]/select[2]/option[text()="1999"]'
                browser.find_element_by_xpath(xpath_m).click()
                browser.find_element_by_xpath(xpath).click()

            elif frequency == 'yearly':
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[2]/select/option[text()="1999"]'
                browser.find_element_by_xpath(xpath).click()

            else:
                raise ValueError('Frequency selection is not treated by code.')

            # fill ending prediction scope (always chooses the last element of the dropdown menu)
            if frequency == 'monthly':
                xpath_m = r'//*[@id="mesReferenciaFinal"]/option[text()="dezembro"]'
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[4]/select[2]'
                browser.find_element_by_xpath(xpath_m).click()

            elif frequency == 'quarterly':
                xpath_m = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[4]/select[1]/option[text()="outubro a dezembro"]'
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[4]/select[2]'
                browser.find_element_by_xpath(xpath_m).click()

            elif frequency == 'yearly':
                xpath = r'//*[@id="form4"]/div[2]/table/tbody[3]/tr/td[4]/select'

            else:
                raise ValueError('Frequency selection is not treated by code.')

            # Pick final option in list (whatever year that is)
            sel = browser.find_element_by_xpath(xpath)
            sel.click()
            options = sel.find_elements_by_tag_name('option')
            options[len(options) - 1].click()

            # click the download button
            xpath = r'//*[@id="btnXLSa"]'
            browser.find_element_by_xpath(xpath).click()

            # saves the time the file was downloaded
            download_save_time = dt.datetime.now()

            # give some time for the download to finish
            time.sleep(6)

            # get the default download directory based on the operating system
            if platform.system() == 'Windows':
                username = os.getlogin()
                download_path = f'C:/Users/{username}/Downloads'

            elif platform.system() == 'Darwin':  # MacOS
                username = getpass.getuser()
                download_path = f'/Users/{username}/Downloads'

            else:
                raise SystemError('This code can only run on Windows or MacOS')

            # reads the downloaded file
            file_path = None
            for (dirpath, dirnames, filenames) in os.walk(download_path):

                for f in filenames:

                    if 'Séries de estatísticas' in f:
                        file_save_time = os.path.getmtime(os.path.join(dirpath, f))
                        file_save_time = dt.datetime.fromtimestamp(file_save_time)

                        if file_save_time > download_save_time:
                            file_path = os.path.join(dirpath, f)

            # read the file and clean the dataframe
            df = pd.read_excel(file_path, skiprows=1, na_values=[' '])

            # delete the 3 last lines of the gdp file because they are comments
            if indicator == 'pib':
                df = df.iloc[:-3]

            # data to datetime and setting data as index
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            df = df.set_index('Data')

            list_df.append(df)

            # clear initial date and end date fo the next loop
            xpath = r'//*[@id="tfDataInicial1"]'
            browser.find_element_by_xpath(xpath).clear()
            xpath = r'//*[@id="tfDataFinal2"]'
            browser.find_element_by_xpath(xpath).clear()

        browser.close()
        df = pd.concat(list_df)
        df = df.drop_duplicates()

        return df
