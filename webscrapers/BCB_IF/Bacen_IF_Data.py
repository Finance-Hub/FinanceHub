# Quantitative Finance
# Insper
# Authors: Ivan Zemella and Renan Pereira

# Imports BancoCentral class
from classes.BancoCentral import BancoCentral

# Imports Pandas class
#import pandas as pd

# Create an object of the Central Bank class
bancoCentral = BancoCentral()
	
continuar = True
	
while(continuar):
		
	trimestre = input('What period do you want to download? ')
	trimestre = trimestre.upper()
	
	indicador_patrimonio_liquido = input('What is the net worth indicator? ') #78186
	indicador_lucro_liquido      = input('What is the net profit indicator? ') #78187

	bancoCentral.obterTrimestre(trimestre,indicador_patrimonio_liquido,indicador_lucro_liquido)
		
	deseja_continuar = input('Continue? [Y/N]       ')
		
	if(deseja_continuar.upper() == 'N'):
		continuar = False

resultado = bancoCentral.obterResultado()


print(resultado)

#df = pd.DataFrame.from_dict(resultado,orient='index')
#df.to_excel(r"df_banks.xlsx")

print('FIM')
		