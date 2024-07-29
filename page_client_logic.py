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
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        query = """
            SELECT 
                job_category,
                SUM(used_mandalecas) as total_used_mandalecas
            FROM delivery_control
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
            GROUP BY job_category
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id, start_date, end_date))
    return df

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
    df = get_clientes()
    cliente = df[df["id"] == cliente_id].iloc[0]
    used_mandalecas_df = get_used_mandalecas(cliente_id, start_date, end_date)

    # Agrupa as mandalecas usadas por categoria
    used_mandalecas = used_mandalecas_df.set_index('job_category').to_dict()['total_used_mandalecas']

    instagram_profile = get_instagram_profile(cliente_id)
    
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
        n_monthly_contracted_content_production_mandalecas = st.number_input("Mandalecas de Produção de Conteúdo Mensais Contratadas", value=cliente['n_monthly_contracted_content_production_mandalecas'])
        n_monthly_contracted_stories_instagram_mandalecas = st.number_input("Mandalecas de Stories Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_stories_instagram_mandalecas'])
        n_monthly_contracted_feed_linkedin_mandalecas = st.number_input("Mandalecas de Feed LinkedIn Mensais Contratadas", value=cliente['n_monthly_contracted_feed_linkedin_mandalecas'])
        n_monthly_contracted_feed_tiktok_mandalecas = st.number_input("Mandalecas de Feed TikTok Mensais Contratadas", value=cliente['n_monthly_contracted_feed_tiktok_mandalecas'])
        n_monthly_contracted_stories_repost_instagram_mandalecas = st.number_input("Mandalecas de Stories Repost Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_stories_repost_instagram_mandalecas'])
        n_monthly_contracted_feed_instagram_mandalecas = st.number_input("Mandalecas de Feed Instagram Mensais Contratadas", value=cliente['n_monthly_contracted_feed_instagram_mandalecas'])
        n_monthly_contracted_trafego_pago_static = st.number_input("Mandalecas de Tráfego Pago Estático Mensais Contratadas", value=cliente['n_monthly_contracted_trafego_pago_static'])
        n_monthly_contracted_trafego_pago_animated = st.number_input("Mandalecas de Tráfego Pago Animado Mensais Contratadas", value=cliente['n_monthly_contracted_trafego_pago_animated'])

        accumulated_creative_mandalecas = st.number_input("Mandalecas Criativas Acumuladas", value=cliente['accumulated_creative_mandalecas'])
        accumulated_format_adaptation_mandalecas = st.number_input("Mandalecas de Adaptação de Formato Acumuladas", value=cliente['accumulated_format_adaptation_mandalecas'])
        accumulated_content_production_mandalecas = st.number_input("Mandalecas de Produção de Conteúdo Acumuladas", value=cliente['accumulated_content_production_mandalecas'])
        accumulated_stories_instagram_mandalecas = st.number_input("Mandalecas de Stories Instagram Acumuladas", value=cliente['accumulated_stories_instagram_mandalecas'])
        accumulated_feed_linkedin_mandalecas = st.number_input("Mandalecas de Feed LinkedIn Acumuladas", value=cliente['accumulated_feed_linkedin_mandalecas'])
        accumulated_feed_tiktok_mandalecas = st.number_input("Mandalecas de Feed TikTok Acumuladas", value=cliente['accumulated_feed_tiktok_mandalecas'])
        accumulated_stories_repost_instagram_mandalecas = st.number_input("Mandalecas de Stories Repost Instagram Acumuladas", value=cliente['accumulated_stories_repost_instagram_mandalecas'])
        accumulated_feed_instagram_mandalecas = st.number_input("Mandalecas de Feed Instagram Acumuladas", value=cliente['accumulated_feed_instagram_mandalecas'])
        accumulated_trafego_pago_static = st.number_input("Mandalecas de Tráfego Pago Estático Acumuladas", value=cliente['accumulated_trafego_pago_static'])
        accumulated_trafego_pago_animated = st.number_input("Mandalecas de Tráfego Pago Animado Acumuladas", value=cliente['accumulated_trafego_pago_animated'])

        if st.button("Atualizar"):
            if not name:
                st.error("O campo 'Nome' não pode ficar em branco.")
            else:
                updated_data = {
                    'name': name,
                    'n_monthly_contracted_creative_mandalecas': n_monthly_contracted_creative_mandalecas,
                    'n_monthly_contracted_format_adaptation_mandalecas': n_monthly_contracted_format_adaptation_mandalecas,
                    'n_monthly_contracted_content_production_mandalecas': n_monthly_contracted_content_production_mandalecas,
                    'n_monthly_contracted_stories_instagram_mandalecas': n_monthly_contracted_stories_instagram_mandalecas,
                    'n_monthly_contracted_feed_linkedin_mandalecas': n_monthly_contracted_feed_linkedin_mandalecas,
                    'n_monthly_contracted_feed_tiktok_mandalecas': n_monthly_contracted_feed_tiktok_mandalecas,
                    'n_monthly_contracted_stories_repost_instagram_mandalecas': n_monthly_contracted_stories_repost_instagram_mandalecas,
                    'n_monthly_contracted_feed_instagram_mandalecas': n_monthly_contracted_feed_instagram_mandalecas,
                    'n_monthly_contracted_trafego_pago_static': n_monthly_contracted_trafego_pago_static,
                    'n_monthly_contracted_trafego_pago_animated': n_monthly_contracted_trafego_pago_animated,
                    'accumulated_creative_mandalecas': accumulated_creative_mandalecas,
                    'accumulated_format_adaptation_mandalecas': accumulated_format_adaptation_mandalecas,
                    'accumulated_content_production_mandalecas': accumulated_content_production_mandalecas,
                    'accumulated_stories_instagram_mandalecas': accumulated_stories_instagram_mandalecas,
                    'accumulated_feed_linkedin_mandalecas': accumulated_feed_linkedin_mandalecas,
                    'accumulated_feed_tiktok_mandalecas': accumulated_feed_tiktok_mandalecas,
                    'accumulated_stories_repost_instagram_mandalecas': accumulated_stories_repost_instagram_mandalecas,
                    'accumulated_feed_instagram_mandalecas': accumulated_feed_instagram_mandalecas,
                    'accumulated_trafego_pago_static': accumulated_trafego_pago_static,
                    'accumulated_trafego_pago_animated': accumulated_trafego_pago_animated,
                }

                update_cliente(cliente_id, updated_data)
                st.success("Dados do cliente atualizados com sucesso!")
        
        st.header("Perfil do Instagram")
        user_name = st.text_input("Nome de Usuário", instagram_profile['user_name'] if instagram_profile else "")
        official_hashtags = st.text_area("Hashtags Oficiais", ", ".join(instagram_profile['official_hashtags']) if instagram_profile else "")
        
        if st.button("Atualizar Perfil do Instagram"):
            update_instagram_profile(cliente_id, user_name, official_hashtags.split(", "))
            st.success("Perfil do Instagram atualizado com sucesso!")
        
        # Exibir tabela de dados
        st.subheader("Detalhes das Mandalecas")
        dados = {
            "Cliente": [cliente['name']],
            "Mandalecas Contratadas Criação": [cliente['n_monthly_contracted_creative_mandalecas']],
            "Mandalecas Usadas Criação": [used_mandalecas.get(JobCategoryEnum.CRIACAO.value, 0)]
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
    cliente_id = 1 

# Código principal para executar a função show_cliente com exemplo de dados
if __name__ == "__main__":
    cliente_id = 1  # Exemplo de ID do cliente
    start_date = '2023-01-01'  # Data de início de exemplo
    end_date = '2023-12-31'  # Data de término de exemplo
    show_cliente(cliente_id, start_date, end_date)
