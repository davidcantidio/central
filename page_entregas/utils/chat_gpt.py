import os

# Caminho da pasta que você quer percorrer
caminho_projeto = '/home/debrito/Documentos/central/page_entregas'

# Arquivo de saída onde será salvo o conteúdo
arquivo_saida = 'resumo_projeto.txt'

def gerar_resumo(caminho, arquivo_saida):
    with open(arquivo_saida, 'w') as f_out:
        # Percorre todas as subpastas e arquivos
        for pasta_atual, subpastas, arquivos in os.walk(caminho):
            for arquivo in arquivos:
                # Caminho completo do arquivo
                caminho_arquivo = os.path.join(pasta_atual, arquivo)
                
                # Somente arquivos com extensão .py
                if arquivo.endswith('.py'):
                    # Escreve o caminho do arquivo no formato desejado
                    f_out.write(f"# {os.path.relpath(pasta_atual, caminho)} - {arquivo}\n\n")

                    # Abre o arquivo e lê o conteúdo
                    with open(caminho_arquivo, 'r') as f_in:
                        conteudo = f_in.read()
                        f_out.write(conteudo)
                    
                    # Adiciona uma quebra de linha entre os arquivos
                    f_out.write("\n\n")

    print(f"Resumo gerado em {arquivo_saida}")

# Executa a função para gerar o resumo
gerar_resumo(caminho_projeto, arquivo_saida)
