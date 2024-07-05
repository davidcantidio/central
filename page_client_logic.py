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
                accumulated_creative_mandalecas = ?, 
                accumulated_format_adaptation_mandalecas = ?, 
                accumulated_content_production_mandalecas = ?
            WHERE id = ?
        """, (
            updated_data['name'], 
            updated_data['n_monthly_contracted_creative_mandalecas'], 
            updated_data['n_monthly_contracted_format_adaptation_mandalecas'], 
            updated_data['n_monthly_contracted_content_production_mandalecas'], 
            updated_data['accumulated_creative_mandalecas'], 
            updated_data['accumulated_format_adaptation_mandalecas'], 
            updated_data['accumulated_content_production_mandalecas'], 
            cliente_id
        ))
        conn.commit()

# Função para obter as mandalecas usadas dos controles de entrega
def get_used_mandalecas(cliente_id, start_date, end_date):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        query_creative = """
            SELECT 
                SUM(used_creative_mandalecas) as mandalecas_criacao,
                SUM(used_format_adaptation_mandalecas) as mandalecas_adaptacao,
                SUM(used_content_mandalecas) as mandalecas_conteudo
            FROM delivery_control_creative
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        query_redes_sociais = """
            SELECT 
                SUM(used_feed_instagram_mandalecas) as mandalecas_feed_instagram,
                SUM(used_reels_instagram_mandalecas) as mandalecas_reels_instagram,
                SUM(used_stories_instagram_mandalecas) as mandalecas_stories_instagram,
                SUM(used_stories_repost_instagram_mandalecas) as mandalecas_stories_repost_instagram,
                SUM(used_feed_linkedin_mandalecas) as mandalecas_feed_linkedin,
                SUM(used_feed_tiktok_mandalecas) as mandalecas_feed_tiktok,
                SUM(used_content_production_mandalecas) as mandalecas_content_production
            FROM delivery_control_redes_social
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        creative_df = pd.read_sql_query(query_creative, conn, params=(cliente_id, start_date, end_date))
        redes_sociais_df = pd.read_sql_query(query_redes_sociais, conn, params=(cliente_id, start_date, end_date))
    return creative_df, redes_sociais_df

# Função para exibir os detalhes do cliente
def show_cliente(cliente_id, start_date, end_date):
    df = get_clientes()
    cliente = df[df["id"] == cliente_id].iloc[0]
    creative_mandalecas, redes_sociais_mandalecas = get_used_mandalecas(cliente_id, start_date, end_date)
    
    st.title(f"Cliente: {cliente['name']}")
    
    with st.sidebar:
        menu = option_menu(
            menu_title="Menu do Cliente",
            options=["Contrato"],
            icons=["file-earmark-text"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

    if menu == "Contrato":
        st.header("Informações do Contrato")
        name = st.text_input("Nome", cliente['name'])
        n_monthly_contracted_creative_mandalecas = st.number_input("Mandaleças Criativas Mensais Contratadas", value=cliente['n_monthly_contracted_creative_mandalecas'])
        n_monthly_contracted_format_adaptation_mandalecas = st.number_input("Mandaleças de Adaptação de Formato Mensais Contratadas", value=cliente['n_monthly_contracted_format_adaptation_mandalecas'])
        n_monthly_contracted_content_production_mandalecas = st.number_input("Mandaleças de Conteúdo Mensais Contratadas", value=cliente['n_monthly_contracted_content_production_mandalecas'])
        accumulated_creative_mandalecas = st.number_input("Mandaleças Criativas Acumuladas", value=cliente['accumulated_creative_mandalecas'])
        accumulated_format_adaptation_mandalecas = st.number_input("Mandaleças de Adaptação de Formato Acumuladas", value=cliente['accumulated_format_adaptation_mandalecas'])
        accumulated_content_production_mandalecas = st.number_input("Mandaleças de Conteúdo Acumuladas", value=cliente['accumulated_content_production_mandalecas'])

        if st.button("Atualizar"):
            if not name:
                st.error("O campo 'Nome' não pode ficar em branco.")
            else:
                updated_data = {
                    'name': name,
                    'n_monthly_contracted_creative_mandalecas': n_monthly_contracted_creative_mandalecas,
                    'n_monthly_contracted_format_adaptation_mandalecas': n_monthly_contracted_format_adaptation_mandalecas,
                    'n_monthly_contracted_content_production_mandalecas': n_monthly_contracted_content_production_mandalecas,
                    'accumulated_creative_mandalecas': accumulated_creative_mandalecas,
                    'accumulated_format_adaptation_mandalecas': accumulated_format_adaptation_mandalecas,
                    'accumulated_content_production_mandalecas': accumulated_content_production_mandalecas
                }
                update_cliente(cliente_id, updated_data)
                st.success("Dados do cliente atualizados com sucesso!")
        
        # Exibir mandalecas usadas
        st.subheader("Mandalecas Usadas")
        st.write(f"Criação: {creative_mandalecas['mandalecas_criacao'].values[0]}")
        st.write(f"Adaptação: {creative_mandalecas['mandalecas_adaptacao'].values[0]}")
        st.write(f"Conteúdo: {creative_mandalecas['mandalecas_conteudo'].values[0]}")
        st.write(f"Feed Instagram: {redes_sociais_mandalecas['mandalecas_feed_instagram'].values[0]}")
        st.write(f"Reels Instagram: {redes_sociais_mandalecas['mandalecas_reels_instagram'].values[0]}")
        st.write(f"Stories Instagram: {redes_sociais_mandalecas['mandalecas_stories_instagram'].values[0]}")
        st.write(f"Stories Repost Instagram: {redes_sociais_mandalecas['mandalecas_stories_repost_instagram'].values[0]}")
        st.write(f"Feed LinkedIn: {redes_sociais_mandalecas['mandalecas_feed_linkedin'].values[0]}")
        st.write(f"Feed TikTok: {redes_sociais_mandalecas['mandalecas_feed_tiktok'].values[0]}")
        st.write(f"Produção de Conteúdo: {redes_sociais_mandalecas['mandalecas_content_production'].values[0]}")

        # Exibir tabela de dados
        st.subheader("Detalhes das Mandalecas")
        dados = {
            "Cliente": [cliente['name']],
            "Mandalecas Contratadas Criação": [cliente['n_monthly_contracted_creative_mandalecas']],
            "Mandalecas Usadas Criação": [creative_mandalecas['mandalecas_criacao'].values[0]]
        }
        df_tabela = pd.DataFrame(dados)
        st.table(df_tabela)
