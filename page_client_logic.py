import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu  # Certifique-se de importar a função option_menu


# Função para obter clientes do banco de dados
def get_clientes():
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        df = pd.read_sql_query("SELECT * FROM clients", conn)
    return df

# Função para atualizar o cliente no banco de dados
def update_cliente(cliente_id, updated_data):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients
            SET name = ?, 
                n_monthly_contracted_creative_mandalecas = ?, 
                n_monthly_contracted_format_adaptation_mandalecas = ?, 
                n_monthly_contracted_content_production_mandalecas = ?, 
                n_monthly_contracted_stories_instagram_mandalecas = ?, 
                n_monthly_contracted_feed_linkedin_mandalecas = ?, 
                n_monthly_contracted_feed_tiktok_mandalecas = ?, 
                n_monthly_contracted_stories_repost_instagram_mandalecas = ?, 
                n_monthly_contracted_reels_instagram_mandalecas = ?, 
                n_monthly_contracted_feed_instagram_mandalecas = ?, 
                accumulated_creative_mandalecas = ?, 
                accumulated_format_adaptation_mandalecas = ?, 
                accumulated_content_production_mandalecas = ?, 
                accumulated_stories_instagram_mandalecas = ?, 
                accumulated_feed_linkedin_mandalecas = ?, 
                accumulated_feed_tiktok_mandalecas = ?, 
                accumulated_stories_repost_instagram_mandalecas = ?, 
                accumulated_reels_instagram_mandalecas = ?, 
                accumulated_feed_instagram_mandalecas = ?
            WHERE id = ?
        """, (
            updated_data['name'], 
            updated_data['n_monthly_contracted_creative_mandalecas'], 
            updated_data['n_monthly_contracted_format_adaptation_mandalecas'], 
            updated_data['n_monthly_contracted_content_production_mandalecas'], 
            updated_data['n_monthly_contracted_stories_instagram_mandalecas'], 
            updated_data['n_monthly_contracted_feed_linkedin_mandalecas'], 
            updated_data['n_monthly_contracted_feed_tiktok_mandalecas'], 
            updated_data['n_monthly_contracted_stories_repost_instagram_mandalecas'], 
            updated_data['n_monthly_contracted_reels_instagram_mandalecas'], 
            updated_data['n_monthly_contracted_feed_instagram_mandalecas'], 
            updated_data['accumulated_creative_mandalecas'], 
            updated_data['accumulated_format_adaptation_mandalecas'], 
            updated_data['accumulated_content_production_mandalecas'], 
            updated_data['accumulated_stories_instagram_mandalecas'], 
            updated_data['accumulated_feed_linkedin_mandalecas'], 
            updated_data['accumulated_feed_tiktok_mandalecas'], 
            updated_data['accumulated_stories_repost_instagram_mandalecas'], 
            updated_data['accumulated_reels_instagram_mandalecas'], 
            updated_data['accumulated_feed_instagram_mandalecas'], 
            cliente_id
        ))
        conn.commit()

def get_used_mandalecas(cliente_id, start_date, end_date):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        query = """
            SELECT 
                SUM(used_creative_mandalecas) as creative_mandalecas,
                SUM(used_format_adaptation_mandalecas) as format_adaptation_mandalecas,
                SUM(used_content_production_mandalecas) as content_production_mandalecas,
                SUM(used_feed_instagram_mandalecas) as feed_instagram_mandalecas,
                SUM(used_reels_instagram_mandalecas) as reels_instagram_mandalecas,
                SUM(used_stories_instagram_mandalecas) as stories_instagram_mandalecas,
                SUM(used_stories_repost_instagram_mandalecas) as stories_repost_instagram_mandalecas,
                SUM(used_feed_linkedin_mandalecas) as feed_linkedin_mandalecas,
                SUM(used_feed_tiktok_mandalecas) as feed_tiktok_mandalecas
            FROM delivery_control
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id, start_date, end_date))
    
    return df

def show_cliente(cliente_id, start_date, end_date):
    df = get_clientes()
    cliente = df[df["id"] == cliente_id].iloc[0]
    used_mandalecas = get_used_mandalecas(cliente_id, start_date, end_date).iloc[0]
    
    st.title(f"Cliente: {cliente['name']}")
    
    with st.sidebar:
        menu = option_menu(
            menu_title="Menu do Cliente",
            options=["Início", "Briefings", "Planos", "Campanhas"],
            icons=["house", "file-text", "map", "bullhorn"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

    if menu == "Início":
        st.header("Informações do Cliente")
        name = st.text_input("Nome", cliente['name'])
        n_monthly_contracted_creative_mandalecas = st.number_input("Mandalecas Criativas Mensais Contratadas", value=cliente['n_monthly_contracted_creative_mandalecas'])
        n_monthly_contracted_format_adaptation_mandalecas = st.number_input("Mandalecas de Adaptação de Formato Mensais Contratadas", value=cliente['n_monthly_contracted_format_adaptation_mandalecas'])
        n_monthly_contracted_content_production_mandalecas = st.number_input("Mandalecas de Conteúdo Mensais Contratadas", value=cliente['n_monthly_contracted_content_production_mandalecas'])
        n_monthly_contracted_stories_instagram_mandalecas = st.number_input("Mandalecas de Stories Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_stories_instagram_mandalecas'])
        n_monthly_contracted_feed_linkedin_mandalecas = st.number_input("Mandalecas de Feed LinkedIn Mensais Contratadas", value=cliente['n_monthly_contracted_feed_linkedin_mandalecas'])
        n_monthly_contracted_feed_tiktok_mandalecas = st.number_input("Mandalecas de Feed TikTok Mensais Contratadas", value=cliente['n_monthly_contracted_feed_tiktok_mandalecas'])
        n_monthly_contracted_stories_repost_instagram_mandalecas = st.number_input("Mandalecas de Stories Repost Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_stories_repost_instagram_mandalecas'])
        n_monthly_contracted_reels_instagram_mandalecas = st.number_input("Mandalecas de Reels Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_reels_instagram_mandalecas'])
        n_monthly_contracted_feed_instagram_mandalecas = st.number_input("Mandalecas de Feed Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_feed_instagram_mandalecas'])

        accumulated_creative_mandalecas = st.number_input("Mandalecas Criativas Acumuladas", value=cliente['accumulated_creative_mandalecas'])
        accumulated_format_adaptation_mandalecas = st.number_input("Mandalecas de Adaptação de Formato Acumuladas", value=cliente['accumulated_format_adaptation_mandalecas'])
        accumulated_content_production_mandalecas = st.number_input("Mandalecas de Conteúdo Acumuladas", value=cliente['accumulated_content_production_mandalecas'])
        accumulated_stories_instagram_mandalecas = st.number_input("Mandalecas de Stories Instagram Acumuladas", value=cliente['accumulated_stories_instagram_mandalecas'])
        accumulated_feed_linkedin_mandalecas = st.number_input("Mandalecas de Feed LinkedIn Acumuladas", value=cliente['accumulated_feed_linkedin_mandalecas'])
        accumulated_feed_tiktok_mandalecas = st.number_input("Mandalecas de Feed TikTok Acumuladas", value=cliente['accumulated_feed_tiktok_mandalecas'])
        accumulated_stories_repost_instagram_mandalecas = st.number_input("Mandalecas de Stories Repost Instagram Acumuladas", value=cliente['accumulated_stories_repost_instagram_mandalecas'])
        accumulated_reels_instagram_mandalecas = st.number_input("Mandalecas de Reels Instagram Acumuladas", value=cliente['accumulated_reels_instagram_mandalecas'])
        accumulated_feed_instagram_mandalecas = st.number_input("Mandalecas de Feed Instagram Acumuladas", value=cliente['accumulated_feed_instagram_mandalecas'])

        if st.button("Atualizar"):
            if not name:
                st.error("O campo 'Nome' não pode ficar em branco.")
            else:
                updated_data = {
                    'name': name,
                    'n_monthly_contracted_creative_mandalecas': n_monthly_contracted_creative_mandalecas,
                    'n_monthly_contracted_format_adaptation_mandalecas': n_monthly_contracted_format_adaptation_mandalecas,
                    'n_monthly_contracted_content_production_mandalecas': n_monthly_contracted_content_production_mandalecas,
                    "n_monthly_contracted_stories_instagram_mandalecas": n_monthly_contracted_stories_instagram_mandalecas,
                    "n_monthly_contracted_feed_linkedin_mandalecas": n_monthly_contracted_feed_linkedin_mandalecas,
                    "n_monthly_contracted_feed_tiktok_mandalecas": n_monthly_contracted_feed_tiktok_mandalecas,
                    "n_monthly_contracted_stories_repost_instagram_mandalecas": n_monthly_contracted_stories_repost_instagram_mandalecas,
                    "n_monthly_contracted_reels_instagram_mandalecas": n_monthly_contracted_reels_instagram_mandalecas,
                    "n_monthly_contracted_feed_instagram_mandalecas": n_monthly_contracted_feed_instagram_mandalecas,

                    'accumulated_creative_mandalecas': accumulated_creative_mandalecas,
                    'accumulated_format_adaptation_mandalecas': accumulated_format_adaptation_mandalecas,
                    'accumulated_content_production_mandalecas': accumulated_content_production_mandalecas,
                    "accumulated_stories_instagram_mandalecas": accumulated_stories_instagram_mandalecas,
                    "accumulated_feed_linkedin_mandalecas": accumulated_feed_linkedin_mandalecas,
                    "accumulated_feed_tiktok_mandalecas": accumulated_feed_tiktok_mandalecas,
                    "accumulated_stories_repost_instagram_mandalecas": accumulated_stories_repost_instagram_mandalecas,
                    "accumulated_reels_instagram_mandalecas": accumulated_reels_instagram_mandalecas,
                    "accumulated_feed_instagram_mandalecas": accumulated_feed_instagram_mandalecas,
                }
                update_cliente(cliente_id, updated_data)
                st.success("Dados do cliente atualizados com sucesso!")
        
        # Exibir mandalecas usadas
        st.subheader("Mandalecas Usadas")
        st.write(f"Criação: {used_mandalecas['creative_mandalecas']}")
        st.write(f"Adaptação: {used_mandalecas['format_adaptation_mandalecas']}")
        st.write(f"Conteúdo: {used_mandalecas['content_production_mandalecas']}")
        st.write(f"Feed Instagram: {used_mandalecas['feed_instagram_mandalecas']}")
        st.write(f"Reels Instagram: {used_mandalecas['reels_instagram_mandalecas']}")
        st.write(f"Stories Instagram: {used_mandalecas['stories_instagram_mandalecas']}")
        st.write(f"Stories Repost Instagram: {used_mandalecas['stories_repost_instagram_mandalecas']}")
        st.write(f"Feed LinkedIn: {used_mandalecas['feed_linkedin_mandalecas']}")
        st.write(f"Feed TikTok: {used_mandalecas['feed_tiktok_mandalecas']}")
        
        # Exibir tabela de dados
        st.subheader("Detalhes das Mandalecas")
        dados = {
            "Cliente": [cliente['name']],
            "Mandalecas Contratadas Criação": [cliente['n_monthly_contracted_creative_mandalecas']],
            "Mandalecas Usadas Criação": [used_mandalecas['creative_mandalecas']]
        }
        df_tabela = pd.DataFrame(dados)
        st.table(df_tabela)
    elif menu == "Briefings":
        st.header("Briefings")
        st.write("Conteúdo para Briefings")
    elif menu == "Planos":
        st.header("Planos")
        st.write("Conteúdo para Planos")
    elif menu == "Campanhas":
        st.header("Campanhas")
        st.write("Conteúdo para Campanhas")

# Código principal para executar a função show_cliente com exemplo de dados
if __name__ == "__main__":
    cliente_id = 1  # Exemplo de ID do cliente
    start_date = '2023-01-01'  # Data de início de exemplo
    end_date = '2023-12-31'  # Data de término de exemplo
    show_cliente(cliente_id, start_date, end_date)
