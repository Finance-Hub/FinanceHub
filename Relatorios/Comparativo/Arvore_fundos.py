import pandas as pd
from datetime import datetime
import os

def arvore_fundos(ref_date = None):
    base_month = ref_date.month - 1

    path = f'Z:\\Relatórios\\Relatório Comparativo de Performance\\{ref_date.year}\\{ref_date.year}-{ref_date.month:02d}'
    csv_filename = f'{ref_date.year}-{base_month:02d} - BASE MARCIO_mod.csv'
    csv_path = os.path.join(path, csv_filename)
    # caminho_arquivo = os.path.join(path, '2024-01 - BASE MARCIO_mod.csv')

    df=pd.read_csv(csv_path, sep=';', encoding='latin1')
    only_lvl_1 = [
        "MAUA PREV SOCI BNP1",
        "CBS",
        "ECONOMUS",
        "FAELCE",
        "FUCAP",
        "SÃO FRANCISCO",
        "VOLKS PP - PLANO PECULIO",
        "PLANO PAP",
        "PLANO PAP 2",
        "FUND BRASILETROS - PLANO PACV",
        "FUND BRASILETROS - PLANO PCA",
        "PLANO BA BD",
        "PLANO PE BD",
        "PLANO PE CD",
        "PLANO RN CD",
        "PLANO RN BD"
    ]
    only_lvl_2 = [
        "MSD",
        "CYAMPREV",
        "MAUA PREV CD",
        "POSTALIS",
        "GEBSA AVIATION",
        "PLANO PAN CONSOLIDADO",
        "PLANO BA CD",
        "INDUSPREV (6 PLANOS)"
    ]
    only_lvl_3 = [
        "GEBSAPREV E GEENERGIA"]
    special_filters = {
        'CARTEIRA CABESP': lambda df: df[df['Fundo Mãe'].notnull()],
        'MSD': lambda df: df[df['Nível'] == 2],
        'CYAMPREV PLANO I': lambda df: df[df['Nível'] == 2],
        'CYAMPREV PLANO II': lambda df: df[df['Nível'] == 2],
        'MAUA PREV CD': lambda df: df[df['Nível'] == 2],
        'MAUA PREV SOCI BNP1': lambda df: df[df['Nível'] == 1],
        'CBS PLANO 35%': lambda df: df[df['Nível'] == 1],
        'CBS PLANO CBSPREV': lambda df: df[df['Nível'] == 1],
        'CBS PLANO MISTO MILENIO': lambda df: df[df['Nível'] == 1],
        'CBS PLANO SUPLEMENTACAO': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO A': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO ASSITENCIAL': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO B': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO C': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO ECO FAMILIA': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO ECO SAUDE': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO ECO PAMC': lambda df: df[df['Nível'] == 1],
        'ECONOMUS PLANO ECO PREVMAIS': lambda df: df[df['Nível'] == 1],
        'FAELCE PLANO BD': lambda df: df[df['Nível'] == 1],
        'FAELCE PLANO CD': lambda df: df[df['Nível'] == 1],
        'FUCAP BD': lambda df: df[df['Nível'] == 1],
        'SÃO FRANCISCO PLANO BD': lambda df: df[df['Nível'] == 1],
        'SÃO FRANCISCO PLANO CD': lambda df: df[df['Nível'] == 1],
        'SÃO FRANCISCO PLANO SALDADO': lambda df: df[df['Nível'] == 1],
        'POSTALIS BD TOTAL': lambda df: df[(df['Nível'] == 2) & (
            ~df['Fundo Filho'].isin(['POSTALIS ADM', 'POSTALIS BD', 'POSTALPREV', 'POSTALIS CV - PROVISIONADOS']))],
        'POSTALIS CD TOTAL': lambda df: df[(df['Nível'] == 2) & (
            ~df['Fundo Filho'].isin(['POSTALIS ADM', 'POSTALIS BD', 'POSTALPREV', 'POSTALIS CV - PROVISIONADOS']))],
        'GEBSA AVIATION': lambda df: df[df['Nível'] == 2],
        'GEBSAPREV': lambda df: df[df['Nível'] == 3],
        'GEENERGIA': lambda df: df[df['Nível'] == 3],
        'PLANO FIPECQ': lambda df: df[df['Nível'].isin([1, 2]) & (~df['Fundo Filho'].str.contains('BUSSOLA'))],
        'PLANO FIPECQ F PREV': lambda df: df[df['Nível'].isin([1, 2]) & (~df['Fundo Filho'].str.contains('BUSSOLA'))],
        'PREVIPLAN': lambda df: df[(df['Nível'] == 1) & (~df['Fundo Filho'].isin(['LONDRES', 'PARIS', 'MADRID']))] \
            .append(df[(df['Nível'] == 2) & (df['Fundo Mãe'].isin(['LONDRES', 'PARIS', 'MADRID']))]),
        'PRHOSPER': lambda df: df[(df['Nível'] == 2) & (~df['Fundo Filho'].isin(['LYON', 'SHANGHAI']))] \
            .append(df[(df['Nível'] == 3) & (df['Fundo Mãe'].isin(['LYON', 'SHANGHAI']))]),
        'VOLKS PP - PLANO PECULIO': lambda df: df[df['Nível'] == 1],
        'VWPP': lambda df: df[(df['Nível'] == 1) & (~df['Fundo Filho'].isin(['JETTA', 'SANTANA', 'T-CROSS']))] \
            .append(df[(df['Nível'] == 2) & (df['Fundo Filho'].isin(['JETTA', 'SANTANA', 'T-CROSS'])) & (
            ~df['Fundo Filho'].isin(['ITAÚ VW JETTA II']))]) \
            .append(df[(df['Nível'] == 3) & (df['Fundo Filho'].isin(['ITAÚ VW JETTA II']))]),
        'PLANO PAP': lambda df: df[df['Nível'] == 1],
        'PLANO PAP 2': lambda df: df[df['Nível'] == 1],
        'PLANO PAN CONSOLIDADO': lambda df: df[df['Nível'] == 2],
        'FUND BRASILETROS - PLANO PACV': lambda df: df[df['Nível'] == 1],
        'FUND BRASILETROS - PLANO PCA': lambda df: df[df['Nível'] == 1],
        'NÉOS CD': lambda df: df[(df['Nível'] == 1) & (~df['Fundo Filho'].isin(
            ['NÉOS RENDA VARIAVEL', 'NÉOS FUNDO DE INVESTIMENTO EM COTAS DE FUNDO DE INVESTIMENTO MULTIMERCADO',
             'SINERGYE', 'SULAMERICA NÉOS']))] \
            .append(df[(df['Nível'] == 2) & (df['Fundo Mãe'].isin(
            ['NÉOS RENDA VARIAVEL', 'NÉOS FUNDO DE INVESTIMENTO EM COTAS DE FUNDO DE INVESTIMENTO MULTIMERCADO',
             'SINERGYE', 'SULAMERICA NÉOS']))]),
        'PLANO BA BD': lambda df: df[df['Nível'] == 1],
        'PLANO PE BD': lambda df: df[df['Nível'] == 1],
        'PLANO PE CD': lambda df: df[df['Nível'] == 1],
        'PLANO RN CD': lambda df: df[df['Nível'] == 1],
        'PLANO RN BD': lambda df: df[df['Nível'] == 1],
        'PLANO BA CD': lambda df: df[df['Nível'] == 2],
        'INDUSPREV (6 PLANOS)': lambda df: df[df['Nível'] == 2],
        'FIERGSPREVI': lambda df: df[df['Nível'] == 2],
        'PREVIND SESI RS': lambda df: df[df['Nível'] == 2]


    }



    for plano in df['Plano'].unique():
        temp = df[df['Plano']==plano]





if __name__ == '__main__':
    arvore_fundos(ref_date = datetime(2024,4,30))
