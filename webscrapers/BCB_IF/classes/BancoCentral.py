# Quantitative Finance
# Insper
# Authors: Ivan Zemella and Renan Pereira
# Class

import json,requests

class BancoCentral:
	
	url_bancos 	= "https://www3.bcb.gov.br/ifdata/rest/arquivos?nomeArquivo=__trimestre__/cadastro__trimestre___1005.json&{}"
	
	url_valores = "https://www3.bcb.gov.br/ifdata/rest/arquivos?nomeArquivo=__trimestre__/dados__trimestre___1.json&{}"
	
	indicador_patrimonio_liquido = 78186
	
	indicador_lucro_liquido = 78187
	
	colecao = {}
	
	trimestres = ['201503','201506','201509','201512','201603','201606','201609','201612','201703','201706','201709','201712','201803','201806','201809','201812', '201903']


	def obterTrimestre(self,trimestre):
		self.obterBancos(trimestre)
		self.obterValores(trimestre)
		
	
	def obterBancos(self,trimestre):
		
		print('Capturing the banks for the quarter ...',trimestre)
		
		self.colecao[trimestre] = {}

		resposta = requests.get(self.url_bancos.replace('__trimestre__',trimestre))
		
		dados = self.converterJson(resposta)
		
		i = 0
		
		while (i < len(dados)):
			
			indice_banco = int(dados[i]['c0'])

			# Add bank data into the collection
			self.colecao[trimestre][indice_banco] = {"trimestre": trimestre,"banco": dados[i]['c2'], "patrimonio_liquido": 0, "lucro_liquido": 0}

			i += 1 
		
	def obterValores(self,trimestre):
		
		print('Capturing the values for the quarter ...',trimestre)

		resposta = requests.get(self.url_valores.replace('__trimestre__',trimestre))
		
		dados = self.converterJson(resposta)
		
		dados = dados['values']
		
		i = 0
		
		colecao = self.colecao
		
		while (i < len(dados)):
			# Find the id of the bank within the values
			indice_banco = int(dados[i]['e'])

			# Validate if this id already exists
			if (indice_banco in colecao[trimestre]):

				x = 0

				while (x < len(dados[i]['v'])):

					# Get the field identifier
					indicador = int(dados[i]['v'][x]['i'])

					if (indicador == self.indicador_patrimonio_liquido):
						colecao[trimestre][indice_banco]['patrimonio_liquido'] = dados[i]['v'][x]['v']

					if (indicador == self.indicador_lucro_liquido):
						colecao[trimestre][indice_banco]['lucro_liquido'] = dados[i]['v'][x]['v']

					x += 1

			i += 1
			
			self.colecao = colecao
			
	def calcularRoe(self,lucro_liquido, patrimonio_liquido):
		return lucro_liquido / patrimonio_liquido
		
	def converterJson(self,resposta):
		return json.loads(resposta.content)
	
	def obterResultado(self):
		resultado = {}
		i = 0
			
		for key,value in self.colecao.items():
			for k,item in value.items():
				resultado[i] = item
				i += 1
					
		return resultado		
