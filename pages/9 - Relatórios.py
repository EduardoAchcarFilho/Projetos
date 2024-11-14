import pyodbc
import streamlit as st
import pandas as pd
from fpdf import FPDF

# Conexão com o banco de dados
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

# Função para buscar as tarefas no banco de dados
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

# Carregar dados
df = pd.DataFrame(tarefas())

# Título da página
st.title("Gerador - Relatórios de Tarefas")

# Sidebar para filtros
with st.sidebar:
    st.header("Opções de Relatório")
    
    # Filtros de multiselect para Cliente, Sistema, Prioridade e Status
    cliente_opcao = st.multiselect('Selecione o(s) Cliente(s)', options=df['Cliente'].unique())
    sistema_opcao = st.multiselect('Selecione o(s) Sistema(s)', options=df['Software/Módulo'].unique())
    prioridade_opcao = st.multiselect('Selecione a Prioridade', options=df['Prioridade'].unique())
    status_opcao = st.multiselect('Selecione o Status', options=df['Status'].unique())
    satisfa_opcao = st.multiselect('Selecione a Satisfação', options=df['Satisfação'].unique())
    
    # Filtro de data
    data_inicio = st.date_input("Data Inicial da Tarefa", value=pd.to_datetime(df['Dt. Tarefa'].min()))
    data_fim = st.date_input("Data Final da Tarefa", value=pd.to_datetime(df['Dt. Tarefa'].max()))

# Aplicando os filtros ao DataFrame
df_filtrado = df[
    (df['Cliente'].isin(cliente_opcao) if cliente_opcao else True) &
    (df['Software/Módulo'].isin(sistema_opcao) if sistema_opcao else True) &
    (df['Prioridade'].isin(prioridade_opcao) if prioridade_opcao else True) &
    (df['Status'].isin(status_opcao) if status_opcao else True) &
    (df['Satisfação'].isin(satisfa_opcao) if satisfa_opcao else True) &
    (df['Dt. Tarefa'] >= pd.to_datetime(data_inicio)) &
    (df['Dt. Tarefa'] <= pd.to_datetime(data_fim))
]
colunas_selecionadas = st.multiselect("Escolha as colunas para exibir:", df.columns.tolist(), default=df.columns.tolist())

# Exibir DataFrame filtrado
st.write("Relatório Filtrado")
st.dataframe(df_filtrado[colunas_selecionadas])

# Função para converter DataFrame em CSV
def converter_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para gerar PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Tarefas', ln=True, align='C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def adicionar_dados(self, df):
        self.set_font('Arial', '', 10)
        for index, row in df.iterrows():
            self.cell(0, 10, f"ID: {row['ID']} | Cliente: {row['Cliente']} | Sistema: {row['Software/Módulo']} | Prioridade: {row['Prioridade']} | Data: {row['Dt. Tarefa']}", ln=True)

# Função para gerar PDF e permitir download
def gerar_pdf(df):
    pdf = PDF(orientation='L')  # Definir para 'L' para paisagem
    pdf.add_page()
    pdf.adicionar_dados(df)
    
    return pdf.output(dest='S').encode('latin1')  # Retorna o PDF em formato de bytes

# Baixar CSV
csv = converter_csv(df_filtrado)
st.download_button(
    label="Baixar Relatório em CSV",
    data=csv,
    file_name='relatorio_tarefas.csv',
    mime='text/csv',
)

# Baixar PDF
pdf_bytes = gerar_pdf(df_filtrado)
st.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name='relatorio_tarefas.pdf',
    mime='application/pdf',
)