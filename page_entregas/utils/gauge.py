import plotly.graph_objects as go
import streamlit as st

def display_gauge_chart(title, contracted, used, accumulated=0):
    """
    Função para exibir um gráfico de medidor (gauge) que mostra os valores contratados, usados e acumulados.

    :param title: Título do medidor.
    :param contracted: Valor contratado.
    :param used: Valor usado até o momento.
    :param accumulated: Valor acumulado (positivo ou negativo).
    """
    if accumulated < 0:
        # Quando o acumulado é negativo, considera um déficit
        max_value = contracted  # Mantém o max_value como o contratado quando há um déficit
        deficit_start = contracted + accumulated  # Início do déficit (valor menor que o contratado)
        steps = [
            {'range': [0, deficit_start], 'color': "lightgray"},  # Intervalo até o início do déficit
            {'range': [deficit_start, contracted], 'color': "red"}  # Intervalo do déficit
        ]
        accumulated_color = 'red'
    else:
        # Caso contrário, o acumulado é positivo
        max_value = contracted + accumulated
        steps = [
            {'range': [0, contracted], 'color': "lightgray"},
            {'range': [contracted, max_value], 'color': "orange"}
        ]
        accumulated_color = 'orange'

    # Cria o gráfico de medidor (gauge)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=used,
        title={'text': title, 'font': {'size': 20}},
        number={'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "green"},
            'steps': steps,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': contracted
            }
        }
    ))

    # Configura o layout e estilo do gráfico
    fig.update_layout(
        autosize=False,
        width=350,
        height=250,
        margin=dict(l=20, r=20, t=50, b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
            dict(
                x=0.15, y=-0.05, xref='paper', yref='paper',
                text=f"Contratado: {contracted}",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor='center',
                yanchor='top',
                bgcolor='green',
                borderpad=5,
                borderwidth=2,
                bordercolor='rgba(0,0,0,0)',
                opacity=1
            ),
            dict(
                x=0.8, y=-0.05, xref='paper', yref='paper',
                text=f"<b>Acumulado:</b> {accumulated}",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor='center',
                yanchor='top',
                bgcolor=accumulated_color,  # Cor de fundo dinâmica baseada no acumulado
                borderpad=5,
                borderwidth=2,
                bordercolor='rgba(0,0,0,0)',
                opacity=1
            )
        ]
    )

    # Renderiza o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)

