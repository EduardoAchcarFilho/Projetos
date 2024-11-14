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

def tarefas():
    Tar = f"""Select id_task as id, tarefa as tarefa from tarefas"""
    cursor.execute(Tar)
    dados = cursor.fetchall()
    return [item[0] for item in dados]

def Cliente():
    results = []
    Clii1 = f"""Select nome as nome, id_cli as id from clientes order by Nome"""
    cursor.execute(Clii1)
    dados = cursor.fetchall()
    for row in dados:
        results.append(list(row))
    return results

def Sistemas():
    SYS = f"""Select software as nome, id_soft as id from softwares order by software"""
    cursor.execute(SYS)
    dados = cursor.fetchall()
    return [(item[0], item[1]) for item in dados]

def filtrar_dados(dataframe, colunas_selecionadas):
    if colunas_selecionadas:
        dataframe = dataframe[colunas_selecionadas]
    return dataframe

def limpar_inputs():
    st.session_state['KID'] = ''
    st.session_state['KPRI'] = ''
    st.session_state['KATI'] = ''
    st.session_state['KTA'] = ''
    st.session_state['KSOFT'] = ["", ""]
    st.session_state['KDTV'] = None
    st.session_state['KCLI'] = ["", ""]
    st.session_state['KDTT'] = None
    st.session_state['KHR'] = None

def adicionar_tarefa(prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada):
    if not tarefa or not sistema_id or not cliente_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    stu = 'Aberto'
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    cliente_str = cliente[0] if isinstance(cliente, list) else cliente
    dt_versao_str = dt_versao.strftime('%Y-%m-%d')
    
    comando = """INSERT INTO tarefas (Prioridade, Atividade, tarefa, id_sys, sistema, dt_versao_sys, id_cli, cliente, dt_tarefa, Status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    
    parametros = (prioridade, atividade, tarefa, sistema_id, sistema_str, dt_versao_str, cliente_id, cliente_str, dt_tarefa_formatada, stu)
    
    try:
        cursor.execute(comando, parametros)
        conexao.commit()
        st.success('Tarefa adicionada com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao gravar no banco de dados: {e}')

def gravar_tarefa(id_tarefa, prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada):
    if not id_tarefa or not tarefa or not sistema_id or not cliente_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    cliente_str = cliente[0] if isinstance(cliente, list) else cliente
    dt_versao_str = dt_versao.strftime('%d-%m-%Y')
    id_tarefa = int(id_tarefa)
    
    comando = """UPDATE tarefas 
                 SET Prioridade = ?, Atividade = ?, tarefa = ?, id_sys = ?, sistema = ?, dt_versao_sys = ?, 
                     id_cli = ?, cliente = ?, dt_tarefa = ?, Status = 'Aberto'
                 WHERE id_task = ?"""
    
    parametros = (prioridade, atividade, tarefa, sistema_id, sistema_str, dt_versao_str, cliente_id, cliente_str, dt_tarefa_formatada,id_tarefa)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Tarefa gravada com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao atualizar no banco de dados: {e}')   

def excluir_tarefa(id_tarefa):
    if not id_tarefa or not tarefa or not sistema_id or not cliente_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    id_tarefa = int(id_tarefa)
    
    comando = """DELETE FROM tarefas WHERE id_task =?"""
    
    parametros = (id_tarefa)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Tarefa excluida com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao excluir no banco de dados: {e}')         

def validar_campos(prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada):
    if not prioridade:
        st.error("Prioridade é obrigatória.")
        return False
    if not atividade:
        st.error("Atividade é obrigatória.")
        return False
    if not tarefa:
        st.error("Tarefa é obrigatória.")
        return False
    if not sistema_id:
        st.error("IDSistema é obrigatório.")
        return False
    if not sistema:
        st.error("Sistema é obrigatório.")
        return False
    if not dt_versao:
        st.error("Data de versão é obrigatória.")
        return False
    if not cliente_id:
        st.error("IDCliente é obrigatório.")
        return False
    if not cliente:
        st.error("Cliente é obrigatório.")
        return False
    if not dt_tarefa_formatada:
        st.error("Data e hora da tarefa são obrigatórios.")
        return False
    return True      

def formatar_data_para_sql(data_iso):
    try:
        if len(data_iso) < 19:
            raise ValueError("Formato da data está incorreto")
        parte_data = data_iso[:10]
        parte_hora = data_iso[11:19]
        ano = parte_data[:4]
        mes = parte_data[5:7]
        dia = parte_data[8:10]
        parte_data_formatada = f"{dia}-{mes}-{ano}"
        data_formatada = f"{parte_data_formatada} {parte_hora}.000"
        return data_formatada
    except Exception as e:
        return f"Erro ao formatar a data: {e}"     

def buscar_tarefas_filtradas_multiplos_filtros_com_data(tarefa_ids=None, cliente_ids=None, data_selecionada=None):
    if not tarefa_ids and not cliente_ids and not data_selecionada:
        return [], []

    condicoes = []
    parametros = []

    if tarefa_ids:
        placeholders_tarefas = ', '.join('?' for _ in tarefa_ids)
        condicoes.append(f"t.id_task IN ({placeholders_tarefas})")
        parametros.extend(tarefa_ids)

    if cliente_ids:
        placeholders_clientes = ', '.join('?' for _ in cliente_ids)
        condicoes.append(f"t.id_cli IN ({placeholders_clientes})")
        parametros.extend(cliente_ids)

    if data_selecionada:
        condicoes.append("CONVERT(DATE, t.dt_tarefa) = ?")
        parametros.append(data_selecionada)

    condicao_final = ' AND '.join(condicoes)

    comando = f"""
    SELECT 
        t.id_task AS ID,
        t.Prioridade AS Prioridade,
        t.Atividade AS Atividade,
        t.tarefa AS Tarefa,
        s.software AS 'Software/Módulo',
        t.dt_versao_sys AS 'Dt. Versão Sistema',
        c.nome AS Cliente,
        t.dt_tarefa AS 'Dt. tarefa'
    FROM 
        tarefas t
    JOIN 
        softwares s ON t.id_sys = s.id_soft
    JOIN 
        clientes c ON t.id_cli = c.id_cli
    """
    
    if condicoes:
        comando += f" WHERE {condicao_final}"

    cursor.execute(comando, parametros)
    dados = cursor.fetchall()

    colunas = ['ID', 'Prioridade', 'Atividade', 'Tarefa', 'Software/Módulo', 'Dt. Versão Sistema', 'Cliente', 'Dt. tarefa']
    tarefas = [list(item) for item in dados]
    
    return tarefas, colunas

def format_date(date):
    return date.strftime('%d/%m/%Y')

def exibir_dataframe_com_botoes(df):
    for index, row in df.iterrows():
        dt_tarefa = row.get('Dt. tarefa', None)
        if isinstance(dt_tarefa, pd.Timestamp):
            dt_tarefa_str = dt_tarefa.strftime("%Y-%m-%d")
            hr_tarefa = dt_tarefa.strftime("%H:%M")
        else:
            dt_tarefa_str = ''
            hr_tarefa = ''

        df = pd.DataFrame({
        'ID': [row.get('ID', '')],
        'Prioridade': [row.get('Prioridade', '')],
        'Atividade': [row.get('Atividade', '')],
        'Tarefa': [row.get('Tarefa', '')],
        'Software/Módulo': [row.get('Software/Módulo', '')],
        'Dt. Versão Sistema': [row.get('Dt. Versão Sistema', '')],
        'Cliente': [row.get('Cliente', '')],
        'Dt. tarefa': [dt_tarefa_str],
        'Hr. Tarefa': [hr_tarefa]
                           })
        st.session_state['df'] = df
          
def exibir_dataframe_com_session_state(df):
    for index, row in df.iterrows():
        dt_versao = row.get('Dt. Versão Sistema', '')
        dt_versao = pd.to_datetime(dt_versao)
        dt_tarefa = row.get('Dt. tarefa', '')
        dt_tarefa = pd.to_datetime(dt_tarefa)
        hr_tarefa = row.get('Hr. Tarefa', '')
        hr_tarefa = pd.to_datetime(hr_tarefa)
        
        if isinstance(dt_tarefa, pd.Timestamp):
            dt_versao_str = pd.to_datetime(dt_versao, format="%Y/%m/%d").date()
            dt_tarefa_str = pd.to_datetime(dt_tarefa, format="%Y/%m/%d").date()
            hr_tarefa_str = pd.to_datetime(hr_tarefa, format="%H:%M").time()
        else:
            dt_versao_str = ''
            dt_tarefa_str = ''
            hr_tarefa = ''

        st.session_state['KDTV'] = dt_versao_str
        st.session_state['KDTT'] = dt_tarefa_str
        st.session_state['KHR'] = hr_tarefa_str
        id_value = row.get('ID', '')
        st.session_state['KID'] = str(id_value)    
        st.session_state['KTA'] = row.get('Tarefa', '')
        
        clientec = row.get('Cliente', '')
        clientec_opcoes = Cliente()
        for cliente in clientec_opcoes:
            if clientec == cliente[0]:
                st.session_state['KCLI'] = cliente
                break
        else:
            st.session_state['KCLI'] = clientec_opcoes[0]

        software_modulo = row.get('Software/Módulo', '')
        sistemas_opcoes = Sistemas()
        for sistema in sistemas_opcoes:
            if software_modulo == sistema[0]:
                st.session_state['KSOFT'] = sistema
                break
        else:
            st.session_state['KSOFT'] = sistemas_opcoes[0]

        pric = row.get('Prioridade', '')
        pric_opcoes = ['', 'ALTO', 'MEDIO', 'BAIXO']
        for pri in pric_opcoes:
            if pric == pri:
                st.session_state['KPRI'] = pri
                break
        else:
            st.session_state['KPRI'] = pric_opcoes

        atic = row.get('Atividade', '')
        atic_opcoes = ['', 'Atualização de Sistema(On-Line Clientes)', 'Atualização de Sistema(Presencial Clientes)', 
                              'Testes(Interno)', 'Treinamento(Interno)', 'Treinamento(On-Line Clientes)', 'Treinamento(Presencial Clientes)']
        for ati in atic_opcoes:
            if atic == ati:
                st.session_state['KATI'] = ati
                break
        else:
            st.session_state['KATI'] = atic_opcoes 
                
# Injetando CSS para ajustar o tamanho dos inputs
st.markdown(
    """
    <style>
    .stTextInput {
        width: 20% !important;  /* Ajuste a largura como desejar */
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
    st.session_state['KIDF'] = []
    st.session_state['KCLIF'] = []
    st.session_state['KDTTF'] = []

alterar_disabled = True   
idf = st.sidebar.multiselect("IDs de Tarefas para Filtro", options=tarefas(), format_func=lambda x: str(x), key='KIDF')
clientef = st.sidebar.multiselect("Cliente para Filtro", options=Cliente(), format_func=lambda x: x[0], key='KCLIF')
dttaredaf = st.sidebar.date_input("Dt. Tarefa para Filtro", value=None, disabled=False, key='KDTTF')

if idf and not clientef and not dttaredaf:
    id_filtro = idf if idf else None 
    tarefas_filtradas2, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(tarefa_ids=idf)
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
      if clientef and idf:
        id_filtro = []
else: 
    id_filtro = []        

if clientef and not idf and not dttaredaf:
    cliente_ids_filtro = [cliente[1] for cliente in clientef]
    tarefas_filtradas, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(cliente_ids=cliente_ids_filtro)
    if tarefas_filtradas:
        df_tarefas3 = pd.DataFrame(tarefas_filtradas, columns=colunas)
        if df_tarefas3.shape[0] == 1:
            alterar_disabled = False  
        else:
            alterar_disabled = True
        st.write("Filtro carregado:")
        st.dataframe(df_tarefas3)
        exibir_dataframe_com_botoes(df_tarefas3)
    else:
       if clientef and idf: 
        cliente_ids_filtro = []
else:
    cliente_ids_filtro = [] 

if dttaredaf and not idf and not clientef:
   cliente_ids_filtro = []
   id_filtro = []
   cliente_ids_filtro = [cliente[1] for cliente in clientef] if clientef else []
   dttaredaf1 = dttaredaf.strftime('%d-%m-%Y')
   tarefas_filtradas, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(data_selecionada=dttaredaf1)
   if tarefas_filtradas:
      df_tarefas_filtradas = pd.DataFrame(tarefas_filtradas, columns=colunas)
      if df_tarefas_filtradas.shape[0] == 1:
            alterar_disabled = False  
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas_filtradas)
      exibir_dataframe_com_botoes(df_tarefas_filtradas)  
else:
    cliente_ids_filtro = []      

if clientef and idf and not dttaredaf:
   cliente_ids_filtro = []
   id_filtro = []
   cliente_ids_filtro = [cliente[1] for cliente in clientef] if clientef else []
   tarefas_filtradas, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(tarefa_ids=idf, cliente_ids=cliente_ids_filtro)
   if tarefas_filtradas:
      df_tarefas_filtradas = pd.DataFrame(tarefas_filtradas, columns=colunas)
      if df_tarefas_filtradas.shape[0] == 1:
            alterar_disabled = False 
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas_filtradas)
      exibir_dataframe_com_botoes(df_tarefas_filtradas)  
else:
    cliente_ids_filtro = []         

if clientef and idf and dttaredaf:
   cliente_ids_filtro = []
   id_filtro = []
   cliente_ids_filtro = [cliente[1] for cliente in clientef] if clientef else []
   dttaredaf1 = dttaredaf.strftime('%d-%m-%Y')
   tarefas_filtradas, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(tarefa_ids=idf, cliente_ids=cliente_ids_filtro, data_selecionada=dttaredaf1)
   if tarefas_filtradas:
      df_tarefas_filtradas = pd.DataFrame(tarefas_filtradas, columns=colunas)
      if df_tarefas_filtradas.shape[0] == 1:
            alterar_disabled = False 
      else:
            alterar_disabled = True
      st.write("Filtro carregado:")
      st.dataframe(df_tarefas_filtradas)
      exibir_dataframe_com_botoes(df_tarefas_filtradas)  
else:
    cliente_ids_filtro = []
    
if st.sidebar.button("Alterar", disabled=alterar_disabled):
    exibir_dataframe_com_session_state(st.session_state.get('df', pd.DataFrame())) 
  
st.markdown("<h1 style='text-align: left; color: white;'>📝 Cadastro - Tarefas</h1>", unsafe_allow_html=True)


id_tarefa = st.text_input("Id Tarefa", value='',label_visibility="visible", disabled=True, key='KID')

prioridade = st.selectbox("Prioridade", ['', 'ALTO', 'MEDIO', 'BAIXO'], disabled=False, key='KPRI')
atividade = st.selectbox("Atividade", 
                             ['', 'Atualização de Sistema(On-Line Clientes)', 'Atualização de Sistema(Presencial Clientes)', 
                              'Testes(Interno)', 'Treinamento(Interno)', 'Treinamento(On-Line Clientes)', 'Treinamento(Presencial Clientes)'], 
                             disabled=False, key='KATI')

tarefa = st.text_area("Tarefa", height=50, disabled=False, key='KTA')

sistema = st.selectbox("Software/Módulo", [["", ""]] + Sistemas(), format_func=lambda x: x[0] if x[0] else "Selecione um Software", disabled=False, key='KSOFT')
sistema_id = sistema[1] if sistema[0] else None 

sistema_id_invisivel = sistema_id #ATENÇÃO

col_datav, col_hora = st.columns([1, 1])
with col_datav:
    dt_versao = st.date_input("Dt. Versão Sistema", disabled=False, value=None, key='KDTV')

cliente = st.selectbox("Cliente", [["", ""]] + Cliente(), format_func=lambda x: x[0] if x[0] else "Selecione um cliente", disabled=False, key='KCLI')
cliente_id = cliente[1] if cliente[0] else None

cliente_id_invisivel = cliente_id #ATENÇÃO

col_data, col_hora = st.columns([1, 1])
with col_data:
    dt_tarefa = st.date_input("Dt. Tarefa", value=None, disabled=False, key='KDTT')
with col_hora:
    hr_tarefa = st.time_input("Hora Tarefa", value=None, disabled=False, key='KHR')

col1, col2, col3= st.columns([1, 1, 1.3])
with col1:
        if st.button("Adicionar Tarefa"):
            if hr_tarefa:
                dt_tarefa_completa = datetime.combine(dt_tarefa, hr_tarefa)
                dt_tarefa_formatada = dt_tarefa_completa.strftime("%Y-%m-%d %H:%M:%S.000")
                dt_tarefa_formatada2 = formatar_data_para_sql(dt_tarefa_formatada)
                dt_tarefa_formatada = dt_tarefa_formatada2
            else:
                dt_tarefa_formatada = None

            if validar_campos(prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada):
                adicionar_tarefa(prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada)

with col2:
        if st.button("Gravar Alterações", disabled=False):
            if hr_tarefa:
                dt_tarefa_completa = datetime.combine(dt_tarefa, hr_tarefa)
                dt_tarefa_formatada = dt_tarefa_completa.strftime("%Y-%m-%d %H:%M:%S.000")
                dt_tarefa_formatada3 = formatar_data_para_sql(dt_tarefa_formatada)
                dt_tarefa_formatada = dt_tarefa_formatada3
            else:
                dt_tarefa_formatada = None  
         
            if validar_campos(prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada):
                gravar_tarefa(id_tarefa,prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, cliente_id, cliente, dt_tarefa_formatada)

with col3:
    if st.button("Excluir Tarefa", disabled=False):
        excluir_tarefa(id_tarefa)