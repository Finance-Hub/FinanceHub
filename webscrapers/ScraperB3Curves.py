"""
Authors: José Gonzalez, Rafael Tamanini, Daniel Dantas de Castro
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup

class ScraperB3Curves(object):
    """
    Scrapper for B3 curves.
    Supported curves are:
            *ACC: Ajuste cupom
            *ALD: Alumínio
            *AN: DI x Anbid
            *ANP: Anbid x pré
            *APR: Ajuste pré
            *BRP: IBrX-50
            *CBD: Cobre
            *DCO: Cupom Cambial OC1
            *DIC: DI x IPCA
            *DIM: DI x IGP-M
            *DOC: Cupom limpo
            *DOL: DI x dólar
            *DP: Dólar x pré
            *EUC: DI x euro
            *EUR: Real x euro
            *IAP: IPCA
            *INP: Ibovespa
            *IPR: IGP-M
            *JPY: Real x iene
            *LIB: Libor
            *NID: Níquel
            *PBD: Chumbo
            *PDN: Prob. não default
            *PRE: DI x pré
            *PTX: Real x dólar
            *SDE: Spread Libor Euro x Dólar
            *SLP: Selic x pré
            *SND: Estanho
            *TFP: TBF x pré
            *TP: TR x pré
            *TR: DI x TR
            *ZND: Zinco
            *TODOS: All above
    """
    

    def scrape(self, curve, start_date, end_date):
        """
        :param curve: B3 code for the curve (see list of supported curves)
        :param start_date: should be in american convention mm/dd/yyyy
        :param end_date: should be in american convention mm/dd/yyyy
        :return: DataFrame (if update_db is False) or None
        """

        if not (type(start_date) is str):
            start_date = start_date.strftime('%m/%d/%Y')
        else:
            start_date = pd.to_datetime(start_date).strftime('%m/%d/%Y')

        if not (type(end_date) is str):
            end_date = end_date.strftime('%m/%d/%Y')
        else:
            end_date = pd.to_datetime(end_date).strftime('%m/%d/%Y')

        dfOut = pd.DataFrame(columns = ['Refdate', 'Curve', 'Type', 'Maturity', 'Value'])
        date_list = pd.date_range(start=start_date, end=end_date)

        for d in date_list:

            print('Scraping', curve, 'for date', d.strftime('%m/%d/%Y'))

            df_date = self._scrapecurve_single_date(curve, d)
            if not isinstance(df_date, int):
                dfOut = pd.concat([dfOut, df_date], join='outer')
        
        dfOut2 = dfOut.reset_index(drop = True)
        
        return dfOut2


    def _scrapecurve_single_date(self, curve, dtAux):
        """
        :param curve: B3 code for the curve (see list of supported curves)
        :param date: should be in american convention mm/dd/yyyy
        :return: DataFrame
        """
        
        def replace_all(text, dic):
            for i in dic:
                text = text.replace(i, "")
            textout = text
            return textout
        
        #base url
        strURL = "http://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data=" + str(dtAux.day).zfill(2) + "/" + str(dtAux.month).zfill(2) +"/" + str(dtAux.year) + "&Data1=" + str(dtAux.year) + str(dtAux.month).zfill(2) + str(dtAux.day).zfill(2) + "&slcTaxa=" + curve
        #loading
        response = requests.get(strURL)
        #parcing
        soup = BeautifulSoup(response.text, 'html.parser')
        #def output
        df_date = pd.DataFrame(columns = ['Refdate', 'Curve', 'Type', 'Maturity', 'Value'])
        
        #split what we are looking for, table contents
        tabelas1 = soup.find_all(class_='tabelaConteudo1')
        #exit condition
        if tabelas1 == []: return 0
        tabelas2 = soup.find_all(class_='tabelaConteudo2')
        if curve == "TODOS":
            title = soup.find_all(class_='tabelaTituloEspecial tabelaTitulo')
        else: 
            title = soup.find_all(class_='tabelaTitulo')
            title = title[1:]
            
        subtitle = soup.find_all(class_='tabelaItem')
        
        #load data from even lines
        tabelas1 = [el.get_text() for el in tabelas1]
        #load data from odd lines
        tabelas2 = [el.get_text() for el in tabelas2]
        tabelas1 = tabelas1 + tabelas2
        #load merged title options
        colspan = [int(el["colspan"]) for el in title]
        #load titles
        title = [el.get_text().replace("\r\n\t\t", "") for el in title]
        #repeat when needed
        title = [[el]*colspan[i] for i, el in zip(range(len(title)), title)]
		#unlist
        title = [item for sublist in title for item in sublist]
		#load subtitles
        subtitle = [el.get_text() for el in subtitle]
		#maket it understandable
        repls = ['\r\n','\n','(1)','(2)','(3)','(4)']
        subtitle = [replace_all(el, repls) for el in subtitle]
        
        #loading vars
        iEntry = 0
        iLastEntry = 0
        dbLastMaturity = 0
        dbMaturity = 0
        
        #treating data
        for el in tabelas1:
            if el.isnumeric():
                #here we are starting a new curve maturity
                dbLastMaturity = dbMaturity
                dbMaturity = int(el)
                
                #should we start a new set of curves?
                if dbLastMaturity > dbMaturity:
                    iLastEntry = iEntry
                    #do we finished the set of curves?
                    if iLastEntry == len(title):
                        #shut down
                        iLastEntry = 0
                        iEntry = 0
                else:
                    iEntry = iLastEntry
                    
            else:
                #pick value
                dbValue = float(el.strip().replace("\r\n", "").replace(",", "."))
                #append
                df_date = df_date.append(pd.Series([dtAux, title[iEntry], subtitle[iEntry], dbMaturity, dbValue], index=df_date.columns), ignore_index = True)
                iEntry = iEntry + 1

        #gen output
        #sort file
        df_date = df_date.sort_values(['Refdate', 'Curve', 'Type', 'Maturity'])
        return df_date
        #export .txt file, tab delimited, good and old taxaswap
        #dfOut.to_csv("taxaswap.txt", sep="\t", index = False)
            #aux function
