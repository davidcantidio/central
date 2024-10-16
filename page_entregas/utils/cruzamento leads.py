import pandas as pd

# Função para carregar arquivos TSV codificados em UTF-16
def read_tsv_utf16(filepath):
    try:
        return pd.read_csv(filepath, encoding='utf-16', delimiter='\t')
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return pd.DataFrame()

# Caminhos dos arquivos CSV (TSV)
csv_file_paths_september = [
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_1v4DubD66G7YYil4Y1OYlybPEsVr_Syp5_Leads_2024-08-08_2024-09-29.csv',
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_1hInB0tW3O1P5GaIhf3D4w9HbKWV-nB-r _ CARD 5_Leads_2024-07-31_2024-09-29.csv',
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_1myUh2JRRD0Bu9pCqEnsugy3h23BIzBZl_Leads_2024-08-19_2024-09-29.csv',
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_1o0QgalnZd2PlTUhDN4feHgT4w3FaHfBI_Leads_2024-07-31_2024-09-29.csv',
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_15gcvkHd-POyc9sS9kbUJkXIWd1-TbmUY_Leads_2024-07-31_2024-09-29.csv',
    '/home/debrito/Documentos/cruzamento leads/setembro/IG _ dp_1BGLLvPG8Kfv2ZryJ8yL1KPkiSgjH6UQN_Leads_2024-08-27_2024-09-29.csv'
]

# Carregar o relatório de leads de setembro
september_report_path = '/home/debrito/Documentos/cruzamento leads/setembro/Relatorio mês de Setembro.xlsx'
september_data = pd.read_excel(september_report_path)

# Carregar e combinar os dados CSV
tsv_dataframes_september = [read_tsv_utf16(path) for path in csv_file_paths_september]
tsv_dataframes_september = [df for df in tsv_dataframes_september if not df.empty]  # Remover dataframes vazios
combined_tsv_data_september = pd.concat(tsv_dataframes_september, ignore_index=True)

# Cruzar os dados usando o campo 'email' tanto no Excel quanto nos CSVs
merged_september_data = pd.merge(september_data, combined_tsv_data_september[['email', 'ad_name']], how='left', on='email')

# Exportar o resultado para um arquivo Excel
output_september_file_path = '/home/debrito/Documentos/cruzamento leads/setembro/Merged_Leads_September_Data.xlsx'
merged_september_data.to_excel(output_september_file_path, index=False)

print(f"Arquivo final salvo em: {output_september_file_path}")
