import pandas as pd

# Caminhos dos arquivos
file_path = '/home/debrito/Documentos/central/SEBRAE - Inova Cerrado e Pantanal_Meta_Tabela - Sheet1.csv'
output_file_path = '/home/debrito/Documentos/central/case_when_clauses.txt'

# Carregar o CSV
df = pd.read_csv(file_path)

# Filtrar para a primeira ocorrência de cada "Ad name"
df_unique = df.drop_duplicates(subset=['Ad name'], keep='first')

# Gerar as cláusulas CASE WHEN
case_when_clauses = "CASE\n"
for index, row in df_unique.iterrows():
    case_when_clauses += f"    WHEN Ad name = '{row['Ad name']}' THEN '{row['Ad creative thumbnail URL']}'\n"
case_when_clauses += "END"

# Salvar em um arquivo de texto
with open(output_file_path, 'w') as file:
    file.write(case_when_clauses)
