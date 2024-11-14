import pyodbc
import streamlit as st
from streamlit_calendar import calendar
import subprocess
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

# Função que puxa os dados do banco de dados e retorna um DataFrame
def erro():
    results = []
    
    # Comando SQL para selecionar dados
    comando = """SELECT [id_erro], [erro], [tipo], [id_sys], [sistema], [solucao], [solucaodef] FROM erros"""
    
    # Executando o comando SQL (supondo que você tenha um cursor configurado)
    cursor.execute(comando)
    dados = cursor.fetchall()

    # Definindo os nomes das colunas
    colunas = ['ID', 'Erro', 'Tipo', 'IDSYS', 'Software/Módulo', 'Solução', 'Definitivo']

    # Convertendo os resultados em uma lista de dicionários
    for row in dados:
        result_dict = {colunas[i]: row[i] for i in range(len(colunas))}
        results.append(result_dict)
    
    return results

# Gerar DataFrame a partir da função erro()
df = pd.DataFrame(erro())

# Filtrar tipos sem incluir None
tipos_validos = df['Tipo'].dropna().unique()  # Remove None
tipo_selecionado = st.sidebar.multiselect("Selecione o Tipo", options=tipos_validos , default=tipos_validos)

# Filtrar sistemas sem incluir None
sistemas_validos = df['Software/Módulo'].dropna().unique()  # Remove None
sistema_selecionado = st.sidebar.multiselect("Selecione o Sistema", options=sistemas_validos, default=sistemas_validos)

# Filtrar soluções definitivas sem incluir None
solucoes_validas = df['Definitivo'].dropna().unique()  # Remove None
solucao_definitiva_selecionada = st.sidebar.multiselect("Selecione Solução Definitiva", options=solucoes_validas, default=solucoes_validas)

# Aplicando os filtros no DataFrame
if tipo_selecionado:
    df = df[df['Tipo'].isin(tipo_selecionado)]

if sistema_selecionado:
    df = df[df['Software/Módulo'].isin(sistema_selecionado)]

if solucao_definitiva_selecionada:
    df = df[df['Definitivo'].isin(solucao_definitiva_selecionada)]

st.markdown("<h1 style='text-align: left; color: white;'>📊 Painel de Controle - Erros/Ajustes</h1>", unsafe_allow_html=True)

# Ajustes estéticos para os gráficos
sns.set(style="whitegrid")

col1, col2 = st.columns([1, 1])

with col1:
 # 1. Gráfico da distribuição de erros por Software/Módulo
 plt.figure(figsize=(10, 6))
 software_module_counts = df['Software/Módulo'].value_counts()
 sns.barplot(x=software_module_counts.index, y=software_module_counts.values, palette='Blues_d')
 #plt.title('Distribuição de Erros por Software/Módulo')
 plt.xticks(rotation=45, ha='right')
 plt.ylabel('Número de Erros')
 plt.xlabel('Software/Módulo')
 plt.tight_layout()

 # Exibir o gráfico no Streamlit
 with st.expander("Distribuição de Erros por Software/Módulo", expanded=True):
    st.pyplot(plt)

 # 2. Percentual de Soluções Definitivas versus Não Definitivas
 df_definitivo = df.dropna(subset=['Definitivo'])
 definitivo_counts = df_definitivo['Definitivo'].value_counts()

 # Insight automático para Soluções Definitivas por Tipo
 df_tipo_definitivo = df.dropna(subset=['Definitivo'])
 tipo_definitivo_counts = pd.crosstab(df_tipo_definitivo['Tipo'], df_tipo_definitivo['Definitivo'])
 # Calculando a porcentagem de soluções definitivas ('Sim') para cada tipo
 percent_definitivo_por_tipo = (tipo_definitivo_counts['Sim'] / tipo_definitivo_counts.sum(axis=1)) * 100
 
 plt.figure(figsize=(6, 6))
 plt.pie(definitivo_counts, labels=definitivo_counts.index, autopct='%1.1f%%', colors=['lightcoral', 'skyblue'], startangle=90)
 #plt.title('Percentual de Soluções Definitivas vs Não Definitivas')

 # Exibir o gráfico no Streamlit
 with st.expander("Percentual de Soluções Definitivas vs Não Definitivas", expanded=True):
   st.pyplot(plt)

with col2: 
 # 3. Contagem de erros por tipo
 plt.figure(figsize=(10, 6))
 idsys_counts = df['Tipo'].value_counts()
 sns.barplot(x=idsys_counts.index, y=idsys_counts.values, palette='Greens_d')
 #plt.title('Distribuição de Erros por Tipo')
 plt.ylabel('Número de Erros')
 plt.xlabel('Tipo')
 plt.tight_layout()

 # Exibir o gráfico no Streamlit
 with st.expander("Distribuição de Erros por Tipo", expanded=True):
    st.pyplot(plt)

 # 4. Analisando a relação entre Software/Módulo e Soluções Definitivas
 plt.figure(figsize=(10, 6))
 software_solution = pd.crosstab(df['Software/Módulo'], df['Definitivo'])
 software_solution.plot(kind='bar', stacked=True, color=['skyblue', 'lightcoral'], figsize=(10, 6))
 #plt.title('Soluções Definitivas vs Não Definitivas por Software/Módulo')
 plt.ylabel('Contagem')
 plt.xticks(rotation=45, ha='right')
 plt.tight_layout()

 # Exibir o gráfico no Streamlit
 with st.expander("Soluções Definitivas vs Não Definitivas por Software/Módulo", expanded=True):
     st.pyplot(plt)  

st.header("📋 Insights")

# Obtendo o tipo com a maior proporção de soluções definitivas
tipo_com_mais_definitivo = percent_definitivo_por_tipo.idxmax()
percent_maior_definitivo = percent_definitivo_por_tipo.max()
st.write(f"- O tipo '{tipo_com_mais_definitivo}' tem a maior proporção de soluções definitivas, com aproximadamente {percent_maior_definitivo:.1f}% de soluções definitivas ('Sim').")

# Insight automático para Distribuição de Erros
max_erros = software_module_counts.idxmax()
max_erros_count = software_module_counts.max()
st.write(f"- O software/módulo com mais erros é :'{max_erros}' com {max_erros_count} erros.")

# Insight automático para Soluções Definitivas
percent_definitivo = definitivo_counts['Sim'] / definitivo_counts.sum() * 100
st.write(f"- Aproximadamente {percent_definitivo:.1f}% das soluções são definitivas ('Sim').") 

# Insight automático para Soluções por Software/Módulo
software_definitivo_max = software_solution['Sim'].idxmax()
software_definitivo_max_count = software_solution['Sim'].max()
st.write(f"- O software/módulo :'{software_definitivo_max}' tem o maior número de soluções definitivas com {software_definitivo_max_count} registros.")

# Novo Insight para o tipo "Ajuste" com o total geral de tarefas
total_tarefas = df.shape[0]  # Calcula o total de tarefas no DataFrame
if 'Ajuste' in df['Tipo'].values:
    ajuste_count = df[df['Tipo'] == 'Ajuste'].shape[0]
    st.write(f"- O tipo 'Ajuste' aparece {ajuste_count} vezes no total de {total_tarefas} tarefas registradas.")
else:
    st.write(f"- Não há registros de erros com o tipo 'Ajuste' no total de {total_tarefas} tarefas registradas.")