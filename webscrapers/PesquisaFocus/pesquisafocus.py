from selenium import webdriver

class FocusIPCA(object):
    """
    Classe para puxar os dados de IPCA do focus.
    - Selenium Webdriver
    """

    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()

    def scrape(self, initial_date, end_date):
        pass
