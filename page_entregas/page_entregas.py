import streamlit as st
import pandas as pd
import logging
from sqlalchemy.orm import Session
from common.models import AttentionPoints, Client
from datetime import datetime
import locale
from streamlit_modal import Modal

# Configurar a localidade para português do Brasil
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')  # Para Windows

# Configuração de logging
logging.basicConfig(filename='debug_log.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações iniciais do Streamlit
st.set_page_config(layout="wide")

def page_entregas(engine):
    logging.debug("Entrando na função page_entregas()")

    # ===========================================================
    # Seção de Seletores de Cliente e Intervalo de Datas na Barra Lateral
    # ===========================================================

    st.sidebar.title("Filtros")

    # Obter a lista de clientes
    clientes_df = get_clientes(engine)

    # Verificar se há clientes disponíveis
    if clientes_df.empty:
        st.error("Nenhum cliente disponível.")
        return

    # Inicializar o st.session_state para data_inicio e data_fim, se necessário
    if "data_inicio" not in st.session_state:
        st.session_state["data_inicio"] = datetime.today() - pd.Timedelta(days=30)
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = datetime.today()
    if "cliente_id" not in st.session_state:
        st.session_state["cliente_id"] = clientes_df["id"].iloc[0]

    # Criar um formulário na barra lateral para os seletores
    with st.sidebar.form(key='filters_form'):
        # Seletor de Cliente
        options = clientes_df["id"].tolist()
        selected_index = clientes_df[clientes_df["id"] == st.session_state["cliente_id"]].index[0]
        selected_index = int(selected_index)  # Garantir que seja um int nativo

        cliente_id = st.selectbox(
            "Selecione o Cliente",
            options=options,
            index=selected_index,
            format_func=lambda x: clientes_df[clientes_df["id"] == x]["name"].values[0],
            key="cliente_id"
        )

        # Seletor de Intervalo de Datas
        date_range = st.date_input(
            "Selecione o Intervalo de Datas",
            value=(st.session_state["data_inicio"], st.session_state["data_fim"]),
            key="date_range"
        )

        # Botão para aplicar os filtros
        submit_button = st.form_submit_button(label='Aplicar Filtros')

    # Verifica se o botão foi clicado
    if submit_button:
        # Validar o intervalo de datas
        if isinstance(date_range, tuple) and len(date_range) == 2:
            data_inicio, data_fim = date_range
            # Atualizar o st.session_state com os valores selecionados
            st.session_state["data_inicio"] = data_inicio
            st.session_state["data_fim"] = data_fim
            logging.debug("Filtros aplicados. Reexecutando a página.")
            st.rerun()
        else:
            st.error("Por favor, selecione um intervalo de datas válido.")

    # Log dos valores selecionados
    logging.debug(f"Cliente selecionado: {st.session_state['cliente_id']}")
    logging.debug(f"Data início: {st.session_state['data_inicio']}, Data fim: {st.session_state['data_fim']}")

    # Obter o nome do cliente selecionado
    cliente_nome = clientes_df[clientes_df["id"] == st.session_state["cliente_id"]]["name"].values[0]

    # Exibir o nome do cliente selecionado na página principal
    st.write(f"## Cliente Selecionado: {cliente_nome}")

    # ===========================================================
    # Botão para adicionar ponto de atenção
    # ===========================================================

    add_attention_point_modal(engine)
    # ===========================================================
    # Exibir Pontos de Atenção
    # ===========================================================

    st.write("### Pontos de Atenção")
    display_attention_points_table(
        st.session_state["cliente_id"],
        st.session_state["data_inicio"],
        st.session_state["data_fim"],
        engine
    )

# Função para adicionar um novo ponto de atenção utilizando streamlit-modal
def add_attention_point_modal(engine):
    # Passo 3: Definir o modal
    modal = Modal("Adicionar Novo Ponto de Atenção", key="adicionar_ponto_modal", padding=20, max_width=744)

    # Passo 4: Botão para abrir o modal
    if st.button("Adicionar Ponto de Atenção"):
        modal.open()

    # Passo 5: Exibir o modal se estiver aberto
    if modal.is_open():
        with modal.container():
            st.write("### Novo Ponto de Atenção")
            # Passo 6: Exibir o formulário dentro do modal
            with st.form(key='new_attention_point_form'):
                selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=datetime.today())
                attention_description = st.text_area("Descrição do Ponto de Atenção")
                submit_new = st.form_submit_button(label='Salvar')

                # Manipulação da submissão
                if submit_new:
                    if attention_description:  # Verifica se a descrição não está vazia
                        save_new_attention_point(st.session_state["cliente_id"], selected_date, attention_description, engine)
                        st.success("Ponto de atenção adicionado com sucesso!")
                        modal.close()  # Fechar o modal
                        st.rerun()  # Recarregar a página
                    else:
                        st.error("A descrição do ponto de atenção não pode estar vazia.")

# Função para salvar o novo ponto de atenção no banco de dados
def save_new_attention_point(cliente_id, attention_date, attention_point, engine):
    try:
        with Session(bind=engine) as session:
            new_entry = AttentionPoints(
                client_id=cliente_id,
                date=attention_date,
                attention_point=attention_point
            )
            session.add(new_entry)
            session.commit()  # Commit da nova entrada
            st.success("Ponto de atenção salvo com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar o ponto de atenção: {e}")

# Função para obter a lista de clientes do banco de dados
def get_clientes(engine):
    with Session(bind=engine) as session:
        clientes = session.query(Client).all()
        clientes_df = pd.DataFrame([{'id': c.id, 'name': c.name} for c in clientes])
    return clientes_df

def display_attention_points_table(cliente_id, data_inicio, data_fim, engine):
    """
    Exibe a tabela de pontos de atenção para um cliente, em um intervalo de datas,
    com botões de Editar e Excluir.
    """
    try:
        with Session(bind=engine) as session:
            attention_points = session.query(AttentionPoints).filter(
                AttentionPoints.client_id == cliente_id,
                AttentionPoints.date.between(data_inicio, data_fim)
            ).order_by(AttentionPoints.date.desc()).all()

        if not attention_points:
            st.info("Nenhum ponto de atenção encontrado para o período selecionado.")
        else:
            data = []
            for ap in attention_points:
                data.append({
                    'Data': ap.date.strftime('%d %b. %Y'),
                    'Ponto de Atenção': ap.attention_point,
                    'ID': ap.id
                })

            attention_points_df = pd.DataFrame(data)

            # Inicializar variáveis de estado para edição e exclusão
            if 'edit_item_id' not in st.session_state:
                st.session_state['edit_item_id'] = None
            if 'edit_modal_open' not in st.session_state:
                st.session_state['edit_modal_open'] = False
            if 'delete_item_id' not in st.session_state:
                st.session_state['delete_item_id'] = None

            # Exibir a tabela com botões de ação
            for index, row in attention_points_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 7, 1, 1])
                col1.write(row['Data'])
                col2.write(row['Ponto de Atenção'])
                if col3.button('✏️', key=f'edit_{row["ID"]}', help='Editar'):
                    st.session_state['edit_item_id'] = row['ID']
                    st.session_state['edit_modal_open'] = True  # Abrir modal

                if col4.button('🗑️', key=f'delete_{row["ID"]}', help='Excluir'):
                    st.session_state['delete_item_id'] = row['ID']

            # Processar edição
            if st.session_state['edit_modal_open']:
                edit_modal(engine, st.session_state['edit_item_id'])

            # Processar exclusão
            if st.session_state['delete_item_id'] is not None:
                delete_item(engine, st.session_state['delete_item_id'])

    except Exception as e:
        st.error(f"Erro ao carregar pontos de atenção: {e}")
        logging.error(f"Erro ao carregar pontos de atenção: {e}")


def edit_modal(engine, item_id):
    # Criar e configurar o modal
    modal = Modal("Editar Ponto de Atenção", key=f'edit_modal_{item_id}', padding=20, max_width=744)

    # Exibir modal se o botão de edição foi clicado
    if st.session_state['edit_modal_open']:
        with Session(bind=engine) as session:
            attention_point = session.query(AttentionPoints).get(item_id)

            if attention_point is None:
                st.error("Ponto de atenção não encontrado.")
                st.session_state['edit_modal_open'] = False  # Fechar o modal
                return

            # Exibir o conteúdo do modal
            with modal.container():
                st.write("### Editar Ponto de Atenção")

                # Exibir o formulário para edição
                with st.form(key=f'edit_form_{item_id}'):
                    selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=attention_point.date)
                    attention_description = st.text_area("Descrição do Ponto de Atenção", value=attention_point.attention_point)
                    submit_edit = st.form_submit_button(label='Salvar Alterações')

                    # Processar a edição após a submissão
                    if submit_edit:
                        if attention_description:
                            try:
                                attention_point.date = selected_date
                                attention_point.attention_point = attention_description
                                session.commit()  # Commit da alteração
                                st.success("Ponto de atenção atualizado com sucesso!")
                                st.session_state['edit_item_id'] = None  # Resetar o estado após a edição
                                st.session_state['edit_modal_open'] = False  # Fechar modal
                                st.rerun()  # Recarregar a página para refletir a edição
                            except Exception as e:
                                st.error(f"Erro ao atualizar o ponto de atenção: {e}")
                        else:
                            st.error("A descrição do ponto de atenção não pode estar vazia.")

def delete_item(engine, item_id):
    st.write("### Excluir Ponto de Atenção")
    st.warning("Tem certeza que deseja excluir este ponto de atenção? Esta ação não pode ser desfeita.")
    col1, col2 = st.columns(2)
    with col1:
        confirm_delete = st.button("Excluir", key=f'confirm_delete_{item_id}')
    with col2:
        cancel_delete = st.button("Cancelar", key=f'cancel_delete_{item_id}')

    if confirm_delete:
        try:
            with Session(bind=engine) as session:
                attention_point = session.query(AttentionPoints).get(item_id)
                if attention_point:
                    session.delete(attention_point)  # Deletar o ponto
                    session.commit()  # Commit da exclusão
                    st.success("Ponto de atenção excluído com sucesso!")
                    st.session_state['delete_item_id'] = None  # Reseta o estado após exclusão
                    st.rerun()
                else:
                    st.error("Ponto de atenção não encontrado.")
        except Exception as e:
            st.error(f"Erro ao excluir o ponto de atenção: {e}")
    elif cancel_delete:
        st.info("Operação de exclusão cancelada.")
        st.session_state['delete_item_id'] = None  # Reseta o estado se o usuário cancelar

# Função para salvar um novo ponto de atenção
def save_new_attention_point(cliente_id, attention_date, attention_point, engine):
    """
    Salva um novo ponto de atenção no banco de dados.
    """
    try:
        with Session(bind=engine) as session:
            new_entry = AttentionPoints(
                client_id=cliente_id,
                date=attention_date,
                attention_point=attention_point
            )
            session.add(new_entry)
            session.commit()  # Commit da nova entrada
            logging.info(f"Novo ponto de atenção salvo no banco de dados para o cliente ID {cliente_id}.")
    except Exception as e:
        logging.error(f"Erro ao salvar o ponto de atenção: {e}")
        st.error(f"Erro ao salvar o ponto de atenção: {e}")

# ===========================================================
# Função principal para executar a página
# ===========================================================
if __name__ == "__main__":
    from common.database import create_engine_and_session
    engine = create_engine_and_session()

    # Executar a função principal
    page_entregas(engine)
