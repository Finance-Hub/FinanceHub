from selenium import webdriver
from datetime import *
import pandas as pd


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

        if type(end_date) is str:
            end_date = pd.to_datetime(end_date).strftime('%m/%d/%Y')
        else:
            end_date = end_date.strftime('%m/%d/%Y')

        if int(end_date[6:]) - int(initial_date[6:]) <= 1:
            xpath = r'//*[@id="tfDataInicial7"]'
            browser.find_element_by_xpath(xpath).send_keys(initial_date)

            xpath = r'//*[@id="tfDataFinal8"]'
            browser.find_element_by_xpath(xpath).send_keys(end_date)

        pass
