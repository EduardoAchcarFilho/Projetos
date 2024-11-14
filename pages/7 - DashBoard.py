import pyodbc
import streamlit as st
import plotly.express as px
import pandas as pd

# Conexão com o banco de dados
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

def tarefas():
    results = []

    comando = f"""SELECT [id_task], [tarefa], [id_sys], [sistema], [dt_versao_sys], [altera_sys], 
                         [id_cli], [cliente], [dt_tarefa], [dt_conclusao], [obs], [Status], [Satisfação], 
                         [Motivo], [Atividade], [Prioridade], [dtinicio], [dtfim], [Sla], [Sla_Atingido]
                  FROM tarefas"""
    
    cursor.execute(comando)
    dados = cursor.fetchall()

    colunas = ['ID', 'Tarefa', 'IDSYS', 'Software/Módulo', 'Dt. Versão Sistema', 'Tarefa Feita', 
               'IDCLI', 'Cliente', 'Dt. Tarefa', 'Dt. Conclusão', 'Observação', 'Status', 
               'Satisfação', 'Motivo', 'Atividade', 'Prioridade', 'Dt. Início', 'Dt. Fim', 'SLA', 'SLA Atingido']

    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

def sla():
    results = []

    comando = f"""SELECT 
    Sla_Atingido,
    FORMAT(ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM tarefas where Status = 'Finalizada'), 2), 'N2')  AS porcentagem
        FROM 
    tarefas
        WHERE 
    Sla_Atingido IN ('Sim')
        GROUP BY 
    Sla_Atingido"""

    cursor.execute(comando)
    dados = cursor.fetchall()

    colunas = ['Sla_Atingido', 'porcentagem']

    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

def satisfacao():
    results = []

    comando = f"""SELECT 
    Satisfação,
    FORMAT(ROUND((COUNT(*) * 100.0) / NULLIF((SELECT COUNT(*) FROM tarefas WHERE Status = 'Finalizada'), 0), 2), 'N2') AS porcentagem
       FROM 
    tarefas
       WHERE 
    Satisfação IN ('5 - Muito satisfeito') 
    AND Status = 'Finalizada'  -- Adicione o filtro de status aqui
       GROUP BY 
    Satisfação"""
    
    cursor.execute(comando)
    dados = cursor.fetchall()

    colunas = ['Satisfação', 'porcentagem']

    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

def motivo():
    results = []

    comando = f"""SELECT TOP 1 
    Motivo,
    COUNT(*) AS Frequencia
      FROM 
    tarefas
      WHERE 
    Satisfação = '1 - Muito insatisfeito'
      GROUP BY 
    Motivo
      ORDER BY 
    Frequencia DESC"""
    
    cursor.execute(comando)
    dados = cursor.fetchall()

    colunas = ['Motivo', 'Frequencia']

    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

def motivo2():
    results = []

    comando = f""" SELECT TOP 1 
    Motivo,
    COUNT(*) AS Frequencia
      FROM 
    tarefas
      WHERE 
    Satisfação = '5 - Muito satisfeito'
      GROUP BY 
    Motivo
      ORDER BY 
    Frequencia DESC"""
    
    cursor.execute(comando)
    dados = cursor.fetchall()

    colunas = ['Motivo', 'Frequencia']

    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

def display_metric2(title, subtitle, subtitle2, target, isposi):
    # Exibe a métrica no layout
    st.markdown(f"""
    <div style="border:2px solid #e1e1e1; padding:10px; border-radius:10px; text-align:center; background-color: #f7f9fa;">
        <h3 style="background-color: #00539C; color: white; padding: 5px; border-radius: 5px 5px 0 0;">{title}</h3>
        <p style="font-size: 45px; color: black; font-weight: bold; margin: 0;">{subtitle}</p>
        <p style="color: gray; font-size: 16px; margin-top: -10px;">{subtitle2}</p>
        <p style="font-size: 14px;">Target: {target}; color: black</p>
        <p style="color: Green; font-size: 14px; font-weight: bold;">{isposi}</p>
    </div>
    """, unsafe_allow_html=True)


def display_metric(title, value, subtitle, target, change, is_positive):
    # Condicional para setas e cores
    arrow = "⬆️" if is_positive else "🔻"
    arrow_color = "green" if is_positive else "red"
    
    # Formatação do valor para exibir com porcentagem
    formatted_value = f"{value:.2f}%"  # Aqui, formatamos apenas o número

    # Exibe a métrica no layout
    st.markdown(f"""
    <div style="border:2px solid #e1e1e1; padding:10px; border-radius:10px; text-align:center; background-color: #f7f9fa;">
        <h3 style="background-color: #00539C; color: white; padding: 5px; border-radius: 5px 5px 0 0;">{title}</h3>
        <p style="font-size: 45px; color: black; font-weight: bold; margin: 0;">{formatted_value}</p>
        <p style="color: gray; font-size: 16px; margin-top: -10px;">{subtitle}</p>
        <p style="font-size: 14px;">Target: {target}; color: black</p>
        <p style="color: {arrow_color}; font-size: 14px; font-weight: bold;">Porcentagem: {change}% {arrow}</p>
    </div>
    """, unsafe_allow_html=True)

# Função para converter strings de SLA em minutos
def convert_sla_to_minutes(sla):
    if sla is None:  # Verifica se o valor é None
        return None  # Retorna None se for None
    try:
        # Converte o SLA para um objeto de tempo
        h, m, s = map(int, sla.split(':'))
        # Retorna o total em minutos
        return h * 60 + m + s / 60
    except ValueError:
        return None  # Retorna None se a conversão falhar    

# Carregar dados
df_data = pd.DataFrame(tarefas())
df_sla = pd.DataFrame(sla())
df_satis = pd.DataFrame(satisfacao())
df_moti = pd.DataFrame(motivo())
df_moti2 = pd.DataFrame(motivo2())


# Converter colunas de data para datetime
df_data['Dt. Tarefa'] = pd.to_datetime(df_data['Dt. Tarefa'], errors='coerce')

# Sidebar com filtros
st.sidebar.header("Filtros")

# Converter min_date e max_date para datetime.date
min_date = df_data['Dt. Tarefa'].min().date()
max_date = df_data['Dt. Tarefa'].max().date()
# Filtro por intervalo de datas (converter também para date)
date_range = st.sidebar.slider("Selecione o intervalo de datas", min_value=min_date, max_value=max_date, value=(min_date, max_date))

# Filtro por status
status_options = df_data['Status'].unique().tolist()
status_filter = st.sidebar.multiselect("Filtrar por Status", options=status_options, default=status_options)

# Filtro por prioridade
priority_options = df_data['Prioridade'].unique().tolist()
priority_filter = st.sidebar.multiselect("Filtrar por Prioridade", options=priority_options, default=priority_options)

# Filtro por Software/Módulo
software_options = df_data['Software/Módulo'].unique().tolist()
software_filter = st.sidebar.multiselect("Filtrar por Software/Módulo", options=software_options, default=software_options)

# Aplicar os filtros
df_filtered = df_data[
    (df_data['Dt. Tarefa'].dt.date.between(date_range[0], date_range[1])) &
    (df_data['Status'].isin(status_filter)) &
    (df_data['Prioridade'].isin(priority_filter)) &
    (df_data['Software/Módulo'].isin(software_filter))
]
# Manter gráficos e insights existentes sem alterações

# 1. Gráfico de barras horizontais para a Distribuição de Tarefas por Software/Módulo
software_counts = df_filtered['Software/Módulo'].value_counts().reset_index()
software_counts.columns = ['Software/Módulo', 'Quantidade']
fig_software = px.bar(software_counts, x='Quantidade', y='Software/Módulo', orientation='h',
                      title='Tarefas por Software/Módulo',
                      labels={'Quantidade': 'Número de Tarefas', 'Software/Módulo': 'Software/Módulo'},
                      color_discrete_sequence=['#1f77b4'])

fig_software.update_layout(showlegend=False, title_x=0.5)

# 2. Gráfico de pizza para Distribuição de Tarefas por Status
status_counts = df_filtered['Status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Quantidade']
fig_status = px.pie(status_counts, names='Status', values='Quantidade',
                    title='Status das Tarefas', hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.G10)

fig_status.update_layout(title_x=0.5)

# 3. Gráfico de barras para Satisfação dos Clientes
satisfaction_counts = df_filtered['Satisfação'].value_counts().reset_index()
satisfaction_counts.columns = ['Satisfação', 'Quantidade']
fig_satisfaction = px.bar(satisfaction_counts, x='Satisfação', y='Quantidade',
                          title='Satisfação dos Clientes',
                          labels={'Quantidade': 'Número de Respostas'},
                          color_discrete_sequence=['#ff7f0e'])

fig_satisfaction.update_layout(showlegend=False, title_x=0.5)

# 4. Gráfico de barras para Análise de SLA (SLA Atingido ou Não)
sla_counts = df_filtered['SLA Atingido'].value_counts().reset_index()
sla_counts.columns = ['SLA Atingido', 'Quantidade']
fig_sla = px.bar(sla_counts, x='SLA Atingido', y='Quantidade', title='Tarefas Dentro do SLA',
                 labels={'Quantidade': 'Número de Tarefas', 'SLA Atingido': 'SLA'},
                 color_discrete_sequence=['#2ca02c'])

fig_sla.update_layout(showlegend=False, title_x=0.5)

# 5. Gráfico de linhas para Tarefas ao Longo do Tempo por Software/Módulo
software_time_series = df_filtered.groupby(['Dt. Tarefa', 'Software/Módulo']).size().reset_index(name='Quantidade')
fig_time_series = px.line(software_time_series, x='Dt. Tarefa', y='Quantidade', color='Software/Módulo',
                          title='Tarefas ao Longo do Tempo por Software/Módulo',
                          labels={'Dt. Tarefa': 'Data', 'Quantidade': 'Número de Tarefas'},
                          color_discrete_sequence=px.colors.qualitative.Set2)

fig_time_series.update_layout(title_x=0.5)

# 6. Gráfico de barras para Distribuição de Tarefas por Prioridade
priority_counts = df_filtered['Prioridade'].value_counts().reset_index()
priority_counts.columns = ['Prioridade', 'Quantidade']
fig_priority = px.bar(priority_counts, x='Quantidade', y='Prioridade', orientation='h',
                      title='Tarefas por Prioridade',
                      labels={'Quantidade': 'Número de Tarefas', 'Prioridade': 'Prioridade'},
                      color_discrete_sequence=['#d62728'])

fig_priority.update_layout(showlegend=False, title_x=0.5)


st.markdown("<h1 style='text-align: left; color: white;'>📈 Dashboard</h1>", unsafe_allow_html=True)

# Primeiro, converta a string para um float, substituindo ',' por '.'
media_satisfacao_percent = float(df_satis['porcentagem'].values[0].replace(',', '.'))
media_sla_percent = float(df_sla['porcentagem'].values[0].replace(',', '.'))
motivo_ins = df_moti['Motivo'].values[0]
motivo_sat = df_moti2['Motivo'].values[0]

# Em seguida, converta para int se necessário
media_satisfacao_percent = int(media_satisfacao_percent)
media_sla_percent  = int(media_sla_percent )

target_satisfacao = 95  # Target desejado para Satisfação
target_sla = 95         # Target desejado para SLA

# Verifica se as médias são maiores ou iguais às metas
if media_satisfacao_percent >= target_satisfacao:
   is_positive_satisfacao = True
else:   
   is_positive_satisfacao = False

if media_sla_percent >= target_sla:
   is_positive_sla = True
else:   
   is_positive_sla = False   

# Calculando as mudanças
change_satisfacao = media_satisfacao_percent - target_satisfacao

change_sla = media_sla_percent - target_sla

coll1, coll2, coll3, coll4 = st.columns(4)
with coll1:
    # Chamar a função com os parâmetros corretos
    display_metric(
    'Satisfação',
    media_satisfacao_percent,  # Passa o valor como número
    'Meta 95%',                # Rótulo de referência 
    '95%',        # Valor de referência 
    f"{abs(change_satisfacao):.2f}",  # Delta (mudança)
    is_positive_satisfacao      # Indica se a mudança é positiva
)
with coll2:
    display_metric(
        'SLA',
        media_sla_percent,
        'Meta 95%',
        '95%',
        f"{abs(change_sla):.2f}",
        is_positive_sla
    )

with coll3:
    display_metric2(
        'Top 1 - Motivo',
        'Satisfação',
        motivo_sat,
        '95%',
        isposi = 'Avaliar'
    )      

with coll4:
    display_metric2(
        'Top 1 - Motivo',
        'Insatisfação',
        motivo_ins,
        '95%',
        isposi = 'Verificar'
    )    

st.markdown("""---""")

col1, col2 = st.columns(2)

with col1:
    with st.expander("Satisfação dos Clientes", expanded=True):
       st.plotly_chart(fig_satisfaction)

    with st.expander("Tarefas por Software/Módulo", expanded=True):
       st.plotly_chart(fig_software)

    with st.expander("Tarefas por Prioridade", expanded=True):
       st.plotly_chart(fig_priority)

with col2:
    with st.expander("Tarefas Dentro do SLA", expanded=True):
       st.plotly_chart(fig_sla)

    with st.expander("Status das Tarefas", expanded=True):
       st.plotly_chart(fig_status)

    with st.expander("Tarefas ao Longo do Tempo por Software/Módulo", expanded=True):
       st.plotly_chart(fig_time_series)

# Manter insights
st.header("📋 Insights")
insights = []

# Insight para distribuição de tarefas por Software/Módulo
if software_counts['Quantidade'].max() > 0:
    top_software = software_counts.loc[software_counts['Quantidade'].idxmax()]
    insights.append(f"O software/módulo :'{top_software['Software/Módulo']}' tem a maior quantidade de tarefas ({top_software['Quantidade']}). Isso indica uma possível sobrecarga e a necessidade de revisão de prioridades.")

# Insight para distribuição de tarefas por Status
if status_counts['Quantidade'].max() > 0:
    open_tasks = status_counts.loc[status_counts['Status'] == 'Aberto', 'Quantidade'].values[0]
    total_tasks = status_counts['Quantidade'].sum()
    if open_tasks / total_tasks > 0.5:  # Se mais de 50% das tarefas estão abertas
        insights.append("Mais da metade das tarefas estão abertas, sugerindo que há uma alta carga de trabalho ou possíveis atrasos na finalização.")

if not satisfaction_counts.empty:  # Verifica se o DataFrame não está vazio
    if '1 - Muito insatisfeito' in satisfaction_counts['Satisfação'].values:  # Verifica se '1 - Muito insatisfeito' está presente
        
        # Contagem de "Muito Insatisfeito"
        low_satisfaction = satisfaction_counts.loc[satisfaction_counts['Satisfação'] == '1 - Muito insatisfeito', 'Quantidade'].values[0]
        
        if low_satisfaction > 0:
            # Filtrar o DataFrame para encontrar os IDs das tarefas com '1 - Muito insatisfeito'
            tarefas_insatisfeitas = df_data[df_data['Satisfação'] == '1 - Muito insatisfeito']['ID'].tolist()
            
            # Convertendo a lista de IDs para uma string
            ids_tarefas = ', '.join(map(str, tarefas_insatisfeitas))
            
            # Adicionar o insight com os IDs das tarefas insatisfeitas
            insights.append(
                f"A satisfação baixa dos clientes ({low_satisfaction} respostas) pode indicar áreas que necessitam de melhorias nos serviços prestados. "
                f"IDs das tarefas com baixa satisfação são: {ids_tarefas}."
            )

# Insight para Análise de SLA
if sla_counts['Quantidade'].max() > 0:
    sla_achieved = sla_counts.loc[sla_counts['SLA Atingido'] == 'Sim', 'Quantidade'].values[0]
    if sla_achieved < total_tasks / 2:  # Se menos da metade das tarefas cumpriram o SLA
        insights.append(f"Menos da metade das tarefas foram concluídas dentro do SLA acordado ({sla_achieved} de {total_tasks}). Isso pode necessitar de ações corretivas.")

# Insight para Tarefas ao Longo do Tempo
if not software_time_series.empty:
    recent_trend = software_time_series.groupby('Software/Módulo').tail(1)
    for software in recent_trend['Software/Módulo'].unique():
        trend = recent_trend[recent_trend['Software/Módulo'] == software]
        if trend['Quantidade'].values[0] > 10:  # Se a quantidade de tarefas recentes é alta
            insights.append(f"O software/módulo '{software}' teve um aumento significativo nas tarefas recentes ({trend['Quantidade'].values[0]}).")

# Exibir insights
for insight in insights:
    st.write("- " + insight)

