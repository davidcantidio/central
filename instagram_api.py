import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd

# Carregar as informações de autenticação do arquivo config.json
config_file = 'config.json'
credentials = service_account.Credentials.from_service_account_file(config_file)

# Autenticar-se com o Google Sheets
sheets_service = build('sheets', 'v4', credentials=credentials)

# Autenticar-se com o Google BigQuery
bigquery_client = bigquery.Client(credentials=credentials)

# ID da planilha no Google Sheets
spreadsheet_id = '1-w9SVZIDUDCNKESOwjQL56-o-QwxnqSL4p3d3uZ3MQo'

# Nome da planilha com os dados dos clientes
sheet_name = 'dados do cliente'

# Obter os dados dos clientes
sheet = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
data = sheet.get('values', [])

# Converter os dados em um DataFrame do pandas
df = pd.DataFrame(data[1:], columns=data[0])


import requests

# Função para obter os dados de insights de posts do Instagram
def get_instagram_insights(client_id):
    # Configurar a URL da API do Instagram
    url = f'https://api.instagram.com/v1/users/{client_id}/media/recent/?access_token=YOUR_ACCESS_TOKEN'

    # Fazer a requisição para a API do Instagram
    response = requests.get(url)
    data = response.json()

    # Extrair os dados de insights de posts
    insights = []
    for post in data['data']:
        insights.append({
            'client': client_id,
            'media_id': post['id'],
            'saved': post['saved'],
            'video_views': post['video_views'],
            'reach': post['reach'],
            'engagement': post['engagement'],
            'impressions': post['impressions'],
            'date': post['created_time'],
            'likes': post['likes']['count'],
            'comments': post['comments']['count'],
            'caption': post['caption']['text'],
            'shortcode': post['shortcode'],
            'permalink': post['link'],
            'product_type': post['product_type'],
            'thumbnail': post['images']['thumbnail']['url'],
            'media_url': post['images']['standard_resolution']['url'],
            'shares': post['shares']['count'],
            'media_type': post['type'],
            'updated': post['updated_time'],
            'postTimeStamp': post['created_time'],
            'postDateTime': post['created_time'],
            'imagem': post['images']['standard_resolution']['url'],
            'instagram_id': post['user']['id']
        })

    return insights

# Obter os dados de insights de posts para cada cliente
insights_data = []
for client_id in df['IDInstagram']:
    insights = get_instagram_insights(client_id)
    insights_data.extend(insights)

# Converter os dados em um DataFrame do pandas
insights_df = pd.DataFrame(insights_data)

# Nome da tabela no Google BigQuery
table_name = 'YOUR_TABLE_NAME'

# Enviar os dados para o Google BigQuery
table_ref = bigquery_client.dataset('mandala-362401.instagram_insights').table(table_name)
job_config = bigquery.LoadJobConfig()
job_config.write_disposition = 'WRITE_APPEND'
job = bigquery_client.load_table_from_dataframe(insights_df, table_ref, job_config=job_config)
job.result()