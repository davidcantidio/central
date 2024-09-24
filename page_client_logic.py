import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime
import json

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
                n_monthly_contracted_trafego_pago_static = ?, 
                n_monthly_contracted_trafego_pago_animated = ?, 
                n_monthly_contracted_feed_instagram_mandalecas = ?, 
                accumulated_creative_mandalecas = ?, 
                accumulated_format_adaptation_mandalecas = ?, 
                accumulated_content_production_mandalecas = ?, 
                accumulated_stories_instagram_mandalecas = ?, 
                accumulated_feed_linkedin_mandalecas = ?, 
                accumulated_feed_tiktok_mandalecas = ?, 
                accumulated_stories_repost_instagram_mandalecas = ?, 
                accumulated_feed_instagram_mandalecas = ?, 
                accumulated_trafego_pago_static = ?, 
                accumulated_trafego_pago_animated = ?
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
            updated_data['n_monthly_contracted_feed_instagram_mandalecas'],  # Adicionado o valor aqui
            updated_data['n_monthly_contracted_trafego_pago_static'], 
            updated_data['n_monthly_contracted_trafego_pago_animated'], 
            updated_data['accumulated_creative_mandalecas'], 
            updated_data['accumulated_format_adaptation_mandalecas'], 
            updated_data['accumulated_content_production_mandalecas'], 
            updated_data['accumulated_stories_instagram_mandalecas'], 
            updated_data['accumulated_feed_linkedin_mandalecas'], 
            updated_data['accumulated_feed_tiktok_mandalecas'], 
            updated_data['accumulated_stories_repost_instagram_mandalecas'], 
            updated_data['accumulated_feed_instagram_mandalecas'], 
            updated_data['accumulated_trafego_pago_static'], 
            updated_data['accumulated_trafego_pago_animated'], 
            cliente_id
        ))
        conn.commit()

def get_used_mandalecas(cliente_id, start_date, end_date):
    # Converter as datas para o formato string 'YYYY-MM-DD'
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    query = """
        SELECT job_category, SUM(used_mandalecas) as total_used_mandalecas
        FROM delivery_control
        WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        GROUP BY job_category
    """

    try:
        # Conectando ao banco de dados SQLite
        with sqlite3.connect('common/db_mandala.sqlite') as conn:
            # Executa a consulta SQL com as datas convertidas para string
            df = pd.read_sql_query(query, conn, params=(cliente_id, start_date_str, end_date_str))
        return df

    except Exception as e:
        # Log do erro (pode usar um logger no lugar de print)
        print(f"Erro ao obter mandalecas usadas: {e}")
        return None

# Função para obter perfil do Instagram
def get_instagram_profile(client_id):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        query = """
            SELECT * FROM instagram_profiles WHERE client_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(client_id,))
    return df.iloc[0] if not df.empty else None

# Função para atualizar ou adicionar perfil do Instagram
def update_instagram_profile(client_id, user_name, official_hashtags, insights):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        cursor = conn.cursor()
        profile = get_instagram_profile(client_id)
        if profile is not None:
            cursor.execute("""
                UPDATE instagram_profiles
                SET user_name = ?, official_hashtags = ?, insights = ?, updated_at = ?
                WHERE client_id = ?
            """, (user_name, json.dumps(official_hashtags), json.dumps(insights), datetime.now(), client_id))
        else:
            cursor.execute("""
                INSERT INTO instagram_profiles (client_id, user_name, official_hashtags, insights, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (client_id, user_name, json.dumps(official_hashtags), json.dumps(insights), datetime.now()))
        conn.commit()

# Função para exibir os detalhes do cliente
def show_cliente(cliente_id, start_date, end_date):
    st.write(f"Exibindo dados do cliente {cliente_id} de {start_date} a {end_date}")
    
    # Obter dados das mandalecas usadas
    used_mandalecas_df = get_used_mandalecas(cliente_id, start_date, end_date)
    
    if used_mandalecas_df is not None and not used_mandalecas_df.empty:
        st.write("Mandalecas usadas:")
        st.dataframe(used_mandalecas_df)
    else:
        st.write("Nenhum dado de mandalecas encontrado para o período selecionado.")

# Código principal para executar a função show_cliente com exemplo de dados
if __name__ == "__main__":
    cliente_id = 1 
