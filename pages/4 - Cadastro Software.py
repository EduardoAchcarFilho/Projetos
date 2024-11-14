import pyodbc
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, time
import pandas as pd
 
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

def Sistemas():
    SYS = f"""Select id_soft as id, software as software from softwares"""
    cursor.execute(SYS)
    dados = cursor.fetchall()
    return [(item[0], item[1]) for item in dados]

def filtrar_dados(dataframe, colunas_selecionadas):
    if colunas_selecionadas:
        dataframe = dataframe[colunas_selecionadas]
    return dataframe

def limpar_inputs():
    st.session_state['SID'] = ''
    st.session_state['SOFT'] = ''
    

def adicionar_tarefa(sistema):
    if not sistema:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    comando = """INSERT INTO softwares (software) 
                 VALUES (?)"""
    parametros = (sistema_str)
    
    try:
        cursor.execute(comando, parametros)
        conexao.commit()
        st.success('Software adicionado com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao gravar no banco de dados: {e}')

def gravar_tarefa(sistema_id, sistema):
    if not sistema_id or not sistema:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    sistema_id = int(sistema_id)
    
    comando = """UPDATE softwares 
                 SET software = ?
                 WHERE id_soft = ?"""
    
    parametros = (sistema_str,sistema_id)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Software Salvo com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao atualizar no banco de dados: {e}')   

def excluir_tarefa(sistema_id):
    if not sistema_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_id = int(sistema_id)
    
    comando = """DELETE FROM softwares WHERE id_soft =?"""
    
    parametros = (sistema_id)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Softwares excluido com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao excluir no banco de dados: {e}')         

def validar_campos(sistema):
    if not sistema:
        st.error("Sistema é obrigatório.")
        return False
    return True  

def buscar_software_filtros(software_ids=None,software_str=None):
    if not software_ids and not software_str:
        return [], []

    condicoes = []
    parametros = []

    if software_ids:
        placeholders_idsoftware = ', '.join('?' for _ in software_ids)
        condicoes.append(f"t.id_soft IN ({placeholders_idsoftware})")
        parametros.extend(software_ids)

    if software_str:
        placeholders_software = ', '.join('?' for _ in software_str)
        condicoes.append(f"t.software IN ({placeholders_software})")
        parametros.extend(software_str)    

    condicao_final = ' AND '.join(condicoes)

    comando = f"""
    SELECT 
        t.id_soft AS ID,
        t.software AS 'Software/Módulo'
    FROM 
        softwares t
    """
    
    if condicoes:
        comando += f" WHERE {condicao_final}"   

    cursor.execute(comando, parametros)
    dados = cursor.fetchall()

    colunas = ['ID', 'Software/Módulo']
    tarefas = [list(item) for item in dados]
    
    return tarefas, colunas

def exibir_dataframe_com_botoes(df):
    for index, row in df.iterrows():
    
        df = pd.DataFrame({
        'ID': [row.get('ID', '')],
        'Software/Módulo': [row.get('Software/Módulo', '')],
                           })
        st.session_state['df'] = df

def exibir_dataframe_com_session_state(df):
    for index, row in df.iterrows():

        id_value = row.get('ID', '')
        st.session_state['SID'] = str(id_value)    
        st.session_state['SOFT'] = row.get('Software/Módulo', '')

# Injetando CSS para ajustar o tamanho dos inputs
st.markdown(
    """
    <style>
    .stTextInput {
        width: 30% !important;  /* Ajuste a largura como desejar */
    }
    .stSelectbox {
        width: 70% !important;  /* Ajuste a largura como desejar */
    }
    .stDateInput {
        width: 45% !important;  /* Ajuste a largura como desejar */
    }
    .stTimeInput {
        width: 39% !important;  /* Ajuste a largura como desejar */
    }
    .stTextArea {
        width: 70% !important;  /* Ajuste a largura como desejar */
    }
    .titulo1 {
        font-size: 24px;
        font-family: Arial, sans-serif;
        color: #ffffff;
    }
    .titulo2 {
        font-size: 35px;
        font-family: Verdana, sans-serif;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<h1 class="titulo2">Filtros</h1>', unsafe_allow_html=True)

if st.sidebar.button('Limpar'):
    limpar_inputs() 
    st.session_state['IDF'] = []
    st.session_state['OFTF'] = []

alterar_disabled = True   
ids = st.sidebar.multiselect("IDs dos Softwares para Filtro", options=Sistemas(), format_func=lambda x: str(x[0]), key='IDF')
Softf = st.sidebar.multiselect("Softwares para Filtro", options=Sistemas(), format_func=lambda x: x[1], key='OFTF')    
        
if ids and not Softf:
    id_filtro = [id[0] for id in ids]
    tarefas_filtradas2, colunas = buscar_software_filtros(software_ids=id_filtro)
    if tarefas_filtradas2:
      df_tarefas2 = pd.DataFrame(tarefas_filtradas2, columns=colunas)
      df = pd.DataFrame(df_tarefas2)
      if df_tarefas2.shape[0] == 1:
            alterar_disabled = False 
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas2)
      exibir_dataframe_com_botoes(df_tarefas2)
    else: 
      if Softf and ids:
        id_filtro = []
else: 
    id_filtro = []   

if Softf and not ids:
    Soft_filtro = [item[1] for item in Softf] if Softf else None
    tarefas_filtradas2, colunas = buscar_software_filtros(software_str=Soft_filtro)
    if tarefas_filtradas2:
      df_tarefas2 = pd.DataFrame(tarefas_filtradas2, columns=colunas)
      df = pd.DataFrame(df_tarefas2)
      if df_tarefas2.shape[0] == 1:
            alterar_disabled = False 
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas2)
      exibir_dataframe_com_botoes(df_tarefas2)
    else: 
      if Softf and ids:
        Soft_filtro = []
else: 
    Soft_filtro = [] 

if Softf and ids:
    Soft_filtro = [item[1] for item in Softf] if Softf else None
    id_filtro = [id[0] for id in ids]
    tarefas_filtradas2, colunas = buscar_software_filtros(software_ids=id_filtro,software_str=Soft_filtro)
    if tarefas_filtradas2:
      df_tarefas2 = pd.DataFrame(tarefas_filtradas2, columns=colunas)
      df = pd.DataFrame(df_tarefas2)
      if df_tarefas2.shape[0] == 1:
            alterar_disabled = False 
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas2)
      exibir_dataframe_com_botoes(df_tarefas2)
    else: 
      if Softf and ids:
         Soft_filtro = []
         id_filtro = []
else: 
    Soft_filtro = []
    id_filtro = []      

if st.sidebar.button("Alterar", disabled=alterar_disabled):
    exibir_dataframe_com_session_state(st.session_state.get('df', pd.DataFrame()))          

#st.markdown('<h1 class="titulo2">Cadastro - Softwares</h1>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align: left; color: white;'>🚀 Cadastro - Softwares/Modulos</h1>", unsafe_allow_html=True)

id_software = st.text_input("Id Software", value='',label_visibility="visible", disabled=True, key='SID')

software = st.text_input("Software", value='',label_visibility="visible", disabled=False, key='SOFT') 

col1, col2, col3= st.columns([1, 1, 5])
with col1:
        if st.button("Adicionar Tarefa"):
            if validar_campos(software):
                adicionar_tarefa(software)

with col2:
        if st.button("Gravar Alterações", disabled=False):
                   
            if validar_campos(software):
                gravar_tarefa(id_software,software)

with col3:
    if st.button("Excluir Tarefa", disabled=False):
        excluir_tarefa(id_software)
        