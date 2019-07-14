# Quantitative Finance
# Insper
# Authors: Ivan Zemella and Renan Pereira

# Imports BancoCentral class
from classes.BancoCentral import BancoCentral

# Imports Pandas class
import pandas as pd

escolha = input('Do you want to enter periods manually? Y / N ')

# Converts the choice to uppercase
escolha = escolha.upper()

# Create an object of the Central Bank class
bancoCentral = BancoCentral()

# Automatic Download
if(escolha == 'N'):
	
	i = 0
	
	listaTrimestres = bancoCentral.trimestres
	
	for contador in range(0, len(listaTrimestres)):
		
		trimestre = listaTrimestres[contador]
		
		bancoCentral.obterTrimestre(trimestre)
		
		i += 1

# Manually Download
elif(escolha == 'Y'):
	
	continuar = True
	
	while(continuar):
		
		trimestre = input('Choose the quarter?  ')
		trimestre = trimestre.upper()
		
		bancoCentral.obterTrimestre(trimestre)
		
		deseja_continuar = input('Do you wish to continue? [Y / N]       ')
		
		if(deseja_continuar.upper() == 'N'):
			continuar = False

resultado = bancoCentral.obterResultado()

print(resultado)

df = pd.DataFrame.from_dict(resultado,orient='index')
df.to_excel(r"df_banks.xlsx")

print('FILE EXPORTED SUCCESSFULLY!')

print('END')