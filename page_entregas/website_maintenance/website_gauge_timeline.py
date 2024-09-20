import streamlit as st
from page_entregas.utils.gauge import display_gauge_chart
from page_entregas.utils.timeline import render_timeline_chart_with_multiple_events
from common.models import JobCategoryEnum
from streamlit_extras.stylable_container import stylable_container
from page_entregas.website_maintenance.website_modal  import modal_website_maintenance_open
from datetime import datetime, timedelta
import calendar

# Função para exibir o medidor e a linha do tempo para manutenção de websites
def display_website_maintenance_gauge_and_timeline(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, maintenance_dates):
    st.write("**Manutenção de Website**")

    # Criar colunas para o medidor e a linha do tempo
    col1 = st.container()

    with col1:
        gauge_chart = display_gauge_chart(
            title="Manutenção de Website",
            contracted=mandalecas_contratadas.get(JobCategoryEnum.WEBSITE_MAINTENANCE, 0),
            used=mandalecas_usadas.get(JobCategoryEnum.WEBSITE_MAINTENANCE, 0),
            accumulated=mandalecas_acumuladas.get(JobCategoryEnum.WEBSITE_MAINTENANCE, 0)
        )
        st.plotly_chart(gauge_chart, use_container_width=True)

    # Renderizar a linha do tempo de manutenção de websites
    today = datetime.today()
    deadline_date = today.replace(day=1) + timedelta(days=calendar.monthrange(today.year, today.month)[1] - 1)
    render_timeline_chart_with_multiple_events(today, deadline_date, maintenance_dates)

    # Adicionar botão para abrir o modal e adicionar uma nova data de manutenção
    if st.button("Adicionar Data de Manutenção"):
        modal_website_maintenance_open()
