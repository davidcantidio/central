from google_sheets import update_google_sheets
from instagram_api import get_instagram_media_data
from bigquery import insert_data_to_bigquery

try:
    # Obter dados do Instagram
    instagram_data = get_instagram_media_data()
    
    # Atualizar planilha do Google Sheets
    update_google_sheets(instagram_data)
    
    # Inserir dados no BigQuery
    insert_data_to_bigquery(instagram_data)

    print("Dados inseridos com sucesso no Google Sheets e BigQuery!")

except Exception as e:
    print("Erro: ", e)
