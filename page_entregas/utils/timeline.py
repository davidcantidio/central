# import plotly.graph_objects as go
# import streamlit as st
# import pandas as pd

# def create_timeline_chart(today, deadline_date, event_date=None, event_name="Enviado"):
#     """
#     Cria um gráfico de linha do tempo para exibir prazos e datas de envio.
    
#     :param today: Data atual (datetime object).
#     :param deadline_date: Data do prazo (datetime object).
#     :param event_date: Data do evento, como a data de envio (datetime object), opcional.
#     :param event_name: Nome do evento (ex.: "Enviado"), opcional, padrão é "Enviado".
#     :return: Objeto Plotly figure representando a linha do tempo.
#     """
#     # Gera uma lista com os dias do mês
#     days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=today.replace(day=28) + pd.offsets.MonthEnd(1))]
#     x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

#     # Inicializa as listas de eventos
#     event_dates = [deadline_date.strftime('%Y-%m-%d')]
#     event_colors = ["red"]
#     event_texts = ["Deadline"]

#     if event_date:
#         event_dates.append(event_date.strftime('%Y-%m-%d'))
#         event_colors.append("green")
#         event_texts.append(event_name)

#     fig = go.Figure()

#     # Adiciona a linha do tempo com os dias do mês
#     fig.add_trace(go.Scatter(
#         x=x_values,
#         y=[1] * len(x_values),
#         mode='lines+markers',
#         line=dict(color='lightgrey', width=2),
#         marker=dict(color='lightgrey', size=6),
#         hoverinfo='x',
#         showlegend=False
#     ))

#     # Adiciona os eventos (prazos, envio, etc.) com as legendas
#     for date, color, text in zip(event_dates, event_colors, event_texts):
#         text_position = "top center" if text == event_name else "bottom center"
#         fig.add_trace(go.Scatter(
#             x=[date],
#             y=[1],
#             mode='markers+text',
#             marker=dict(color=color, size=12),
#             text=[text],
#             textposition=text_position,
#             showlegend=False,
#             hoverinfo='none'
#         ))

#     # Configuração do layout do gráfico
#     fig.update_layout(
#         xaxis=dict(
#             tickmode='array',
#             tickvals=x_values,
#             ticktext=[day.strftime('%d') for day in days_in_month],
#             showline=False,
#             showgrid=False,
#             zeroline=False,
#             tickfont=dict(size=10),
#             tickangle=0,
#             ticks='outside',
#             ticklen=4,
#             tickwidth=1,
#         ),
#         yaxis=dict(visible=False),
#         height=95,
#         margin=dict(l=20, r=20, t=10, b=10),
#         plot_bgcolor='rgba(0,0,0,0)',
#         paper_bgcolor='rgba(0,0,0,0)',
#     )

#     return fig

# def render_timeline_chart(today, deadline_date, event_date=None, event_name="Enviado"):
#     """
#     Renderiza o gráfico de linha do tempo no Streamlit.
    
#     :param today: Data atual (datetime object).
#     :param deadline_date: Data do prazo (datetime object).
#     :param event_date: Data do evento, como a data de envio (datetime object), opcional.
#     :param event_name: Nome do evento (ex.: "Enviado"), opcional, padrão é "Enviado".
#     """
#     fig = create_timeline_chart(today, deadline_date, event_date, event_name)
#     st.plotly_chart(fig, use_container_width=True)

# def render_timeline_chart_with_multiple_events(today, deadline_date, event_dates):
#     """
#     Renderiza um gráfico de linha do tempo com múltiplos eventos, como manutenção de websites.
    
#     :param today: Data atual (datetime object).
#     :param deadline_date: Data do prazo (datetime object).
#     :param event_dates: Lista de datas de eventos.
#     """
#     days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=deadline_date)]
#     x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

#     fig = go.Figure()

#     # Adicionando a linha do tempo com os dias do mês
#     fig.add_trace(go.Scatter(
#         x=x_values,
#         y=[1] * len(x_values),
#         mode='lines+markers',
#         line=dict(color='lightgrey', width=2),
#         marker=dict(color='lightgrey', size=6),
#         hoverinfo='x',
#         showlegend=False
#     ))

#     # Adicionando os eventos de manutenção
#     for date in event_dates:
#         fig.add_trace(go.Scatter(
#             x=[date.strftime('%Y-%m-%d')],
#             y=[1],
#             mode='markers+text',
#             marker=dict(color='green', size=12),
#             text=["Manutenção"],
#             textposition="top center",
#             showlegend=False,
#             hoverinfo='none'
#         ))

#     # Configura o layout do gráfico
#     fig.update_layout(
#         xaxis=dict(
#             tickmode='array',
#             tickvals=x_values,
#             ticktext=[day.strftime('%d') for day in days_in_month],
#             showline=False,
#             showgrid=False,
#             zeroline=False,
#             tickfont=dict(size=10),
#             tickangle=0,
#             ticks='outside',
#             ticklen=4,
#             tickwidth=1,
#         ),
#         yaxis=dict(visible=False),
#         height=150,
#         margin=dict(l=20, r=20, t=10, b=10),
#         plot_bgcolor='rgba(0,0,0,0)',
#         paper_bgcolor='rgba(0,0,0,0)',
#     )

#     # Renderiza o gráfico no Streamlit
#     st.plotly_chart(fig, use_container_width=True)
