import pyodbc
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, time, timedelta
import pandas as pd
from PIL import Image
 
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
    Tar = f""" Select id_task as id, tarefa as tarefa, pausas as pausas,Retomadas as Retomadas from tarefas where status <> 'Finalizada' """
    cursor.execute(Tar)
    dados = cursor.fetchall()
    #return [item[0] for item in dados]
    for row in dados:
        results.append(list(row))
    return results

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
    st.session_state['STAT'] = ''
    st.session_state['KPRI'] = ''
    st.session_state['KATI'] = ''
    st.session_state['KTA'] = ''
    st.session_state['KSOFT'] = ["", ""]
    st.session_state['KDTV'] = None
    st.session_state['ATR'] = ''
    st.session_state['KCLI'] = ["", ""]
    st.session_state['KDTT'] = None
    st.session_state['KHR'] = None
    st.session_state['SATIS'] = ''
    st.session_state['MOTI'] = ''
    st.session_state['OBS'] = ''

def gravar_tarefa(status,prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, realizada, cliente_id, cliente, dt_tarefa_formatada,satisfacao,motivo,observacao,id_tarefa):
    if not id_tarefa or not tarefa or not sistema_id or not cliente_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    cliente_str = cliente[0] if isinstance(cliente, list) else cliente
    dt_versao_str = dt_versao.strftime('%d-%m-%Y')
    
    id_tarefa = int(id_tarefa)
    
    comando = """UPDATE tarefas 
                 SET  Status = ?, Prioridade = ?, Atividade = ?, tarefa = ?, id_sys = ?, sistema = ?, dt_versao_sys = ?, altera_sys = ?, 
                     id_cli = ?, cliente = ?, dt_tarefa = ?, Satisfação = ?, Motivo = ?, obs = ?
                 WHERE id_task = ?"""
    
    parametros = (status, prioridade, atividade, tarefa, sistema_id, sistema_str, dt_versao_str, realizada, cliente_id, cliente_str, dt_tarefa_formatada,satisfacao,motivo,observacao,id_tarefa) 

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

def validar_campos(status,prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, realizada, cliente_id, cliente, dt_tarefa_formatada):
    if not status:
        st.error("Status é obrigatória.")
        return False
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
    if not realizada:
        st.error("Tarefa Realizada é obrigatória.")
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
    #if not satisfacao:
    #    st.error("satisfacao da tarefa são obrigatórios.")
    #    return False
    #if not motivo:
    #    st.error("motivo da tarefa são obrigatórios.")
    #    return False
    #if not observacao:
    #    st.error("observacao da tarefa são obrigatórios.")
    #    return False

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
        t.Status as Status,
        t.Prioridade AS Prioridade,
        t.Atividade AS Atividade,
        t.tarefa AS Tarefa,
        s.software AS 'Software/Módulo',
        t.dt_versao_sys AS 'Dt. Versão Sistema',
        t.altera_sys as Realizada,
        c.nome AS Cliente,
        t.dt_tarefa AS 'Dt. tarefa',
        t.Satisfação as Satisfação,
        t.Motivo as Motivo,
        t.obs as Observação
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

    colunas = ['ID','Status','Prioridade', 'Atividade', 'Tarefa', 'Software/Módulo', 'Dt. Versão Sistema', 'Realizada', 'Cliente', 'Dt. tarefa', 'Satisfação', 'Motivo', 'Observação']
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
        'Status':[row.get('Status', '')],
        'Prioridade': [row.get('Prioridade', '')],
        'Atividade': [row.get('Atividade', '')],
        'Tarefa': [row.get('Tarefa', '')],
        'Software/Módulo': [row.get('Software/Módulo', '')],
        'Dt. Versão Sistema': [row.get('Dt. Versão Sistema', '')],
        'Realizada':[row.get('Realizada', '')],
        'Cliente': [row.get('Cliente', '')],
        'Dt. tarefa': [dt_tarefa_str],
        'Hr. Tarefa': [hr_tarefa],
        'Satisfação':[row.get('Satisfação', '')],
        'Motivo':[row.get('Motivo', '')],
        'Observação':[row.get('Observação', '')]
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

        st.session_state['OBS'] = row.get('Observação', '')
        st.session_state['ATR'] = row.get('Realizada', '')
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

        stat = row.get('Status', '')
        stat_opcoes = ['','Aberto','Pausado','Em Execução']
        for stati in stat_opcoes:
            if stat == stati:
                st.session_state['STAT'] = stati
                break
        else:
            st.session_state['STAT'] = stat_opcoes  

        satis = row.get('Satisfação', '')
        satis_opcoes = ['','5 - Muito satisfeito', '4 - Parcialmente satisfeito', '3 - Nem satisfeito, Nem insatisfeito', '2 - Parcialmente insatisfeito', '1 - Muito insatisfeito']
        for satisi in satis_opcoes:
            if satis == satisi:
                st.session_state['SATIS'] = satisi
                break
        else:
            st.session_state['SATIS'] = satis_opcoes   

        moti = row.get('Motivo', '')
        moti_opcoes = ['','1 - Valor','2 - Teste','3 - Suporte ao Sistema','4 - Funções no Sistema','5 - Outros']
        for motii in moti_opcoes:
            if moti == motii:
                st.session_state['MOTI'] = motii
                break
        else:
            st.session_state['MOTI'] = moti_opcoes   

# Função para definir o SLA baseado na prioridade
def definir_sla(prioridade):
    if prioridade == 'ALTO':
        return '00:30:00.000'
    elif prioridade == 'MEDIO':
        return '01:00:00.000'
    elif prioridade == 'BAIXO':
        return '02:00:00.000'
    return None

# Função para iniciar tarefa
def iniciar_tarefa():
    id_tarefa = st.session_state.get('KID', '')
    prioridade = st.session_state.get('KPRI', '')
    
    if id_tarefa == "":
        st.warning('Campos vazios ou inválidos, operação não realizada')
    else:
        if status == 'Em Execução':
           st.warning('Esta Tarefa já esta iniciada')
        else:    
           DtIni = datetime.now()
           Sta = 'Em Execução'
           Sla1 = definir_sla(prioridade)
        
           if Sla1 is None:
               st.warning('Prioridade não definida, operação não realizada')
           else:
               comando = f"""
               UPDATE tarefas 
               SET Status = '{Sta}', dtinicio = CONVERT(DATETIME2, '{DtIni}', 121), Sla = '{Sla1}' 
               WHERE id_task = {id_tarefa}
               """
               cursor.execute(comando)
               conexao.commit()
               st.success('Tarefa Iniciada')  

# Função para pausar a tarefa
def pausar_tarefa():
    global pausas  # Referencia a variável global
    id_tarefa = st.session_state.get('KID', '')
    status_tarefa = st.session_state.get('STAT', '')

    if id_tarefa == "" or status_tarefa != 'Em Execução':
        st.warning('Campos vazios ou inválidos, operação não realizada')
    else:
        DtIni = datetime.now()
        Sta = 'Pausado'

        # Se a lista de pausas estiver vazia, cria a primeira pausa
        if not pausas:
            pausas_str = DtIni.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            # Adiciona a nova pausa à lista de pausas e converte para string
            pausas.append(DtIni.strftime('%Y-%m-%d %H:%M:%S.%f'))
            pausas_str = ",".join(pausas)  # Concatena as pausas em uma string separada por vírgulas

        comando = f"""
        UPDATE tarefas 
        SET Status = '{Sta}', pausas = '{pausas_str}' 
        WHERE id_task = {id_tarefa}
        """

        cursor.execute(comando)
        conexao.commit()
        st.success('Tarefa Pausada')   

# Função para retomar a tarefa
def retomar_tarefa():
    global retomadas  # Referencia a variável global
    id_tarefa = st.session_state.get('KID', '')
    status_tarefa = st.session_state.get('STAT', '')

    if id_tarefa == "" or status_tarefa != 'Pausado':
        st.warning('Campos vazios ou inválidos, operação não realizada')
    else:
        DtIni = datetime.now()
        Sta = 'Em Execução'

        if not retomadas:
            retomadas_str = DtIni.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            retomadas.append(DtIni.strftime('%Y-%m-%d %H:%M:%S.%f'))
            retomadas_str = ",".join(retomadas)  

        comando = f"""
        UPDATE tarefas 
        SET Status = '{Sta}', Retomadas = '{retomadas_str}' 
        WHERE id_task = {id_tarefa}
        """

        cursor.execute(comando)
        conexao.commit()
        st.success('Tarefa ReIniciada') 

# Função para iniciar tarefa
def finalizar_tarefa():
    id_tarefa = st.session_state.get('KID', '')
    prioridade = st.session_state.get('KPRI', '')
    
    if id_tarefa == "":
        st.warning('Campos vazios ou inválidos, operação não realizada')
    else:
        if status == 'Em Execução':
           DtIni = datetime.now()
           Sta = 'Finalizada'
           Sla1 = definir_sla(prioridade)
        
           if Sla1 is None:
               st.warning('Prioridade não definida, operação não realizada')
           else:
               comando = f"""UPDATE tarefas set Status = '{Sta}',dtfim = CONVERT(DATETIME2,'{DtIni}', 121), dt_conclusao = CONVERT(DATETIME2,'{DtIni}', 121) where id_task = {id_tarefa}"""
               cursor.execute(comando)
               conexao.commit()
               st.success('Tarefa Finalizada')
               comando1 = f"""Select dtinicio,dtfim,pausas,Retomadas,Sla from tarefas where id_task = {id_tarefa}"""
               cursor.execute(comando1)
               row = cursor.fetchone()
               if row:
                    datainiciotarefa = row.dtinicio
                    fimdatarefa = row.dtfim
                    pausas_str = row.pausas
                    retomartarefa_str = row.Retomadas
                    sla_str = row.Sla
                    
                    # Converter SLA de string VARCHAR para timedelta
                    sla = varchar_to_timedelta(sla_str)

                    # Calcular SLA
                    tempo_efetivo, sla_atingido = calcular_sla(
                        datainiciotarefa,
                        fimdatarefa,
                        pausas_str,
                        retomartarefa_str,
                        sla
                    )
    
                    #sg.popup(f"Tempo efetivo de trabalho: {tempo_efetivo}")
                    st.success(f"SLA atingido: {'Sim' if sla_atingido else 'Não'}")
                    if sla_atingido == True:
                       comando2 = f"""UPDATE tarefas set Sla_Atingido = 'Sim',Tempo_efetivo = CONVERT(TIME,'{tempo_efetivo}', 121) where id_task = {id_tarefa}""" 
                       cursor.execute(comando2)
                       conexao.commit()
                    else:
                       comando2 = f"""UPDATE tarefas set Sla_Atingido = 'Não',Tempo_efetivo = CONVERT(TIME,'{tempo_efetivo}', 121) where id_task = {id_tarefa}""" 
                       cursor.execute(comando2)
                       conexao.commit() 
        else:    
             st.warning('Esta Tarefa não esta com Status " Em Execução "')   

# Função para converter string VARCHAR para timedelta
def varchar_to_timedelta(sla_str):
    # Suponha que o formato do SLA seja 'HH:MM:SS' ou 'HH:MM:SS.SSS'
    try:
        if sla_str is None:
            return timedelta(0)  # Retorne timedelta zero se SLA for None
        
        if '.' in sla_str:
            h, m, s = sla_str.split(':')
            s, ms = s.split('.')
            milliseconds = int(ms[:3])  # Apenas os primeiros 3 dígitos para milissegundos
        else:
            h, m, s = sla_str.split(':')
            milliseconds = 0
        
        hours = int(h)
        minutes = int(m)
        seconds = int(s)
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    except ValueError as e:
        print(f"Erro ao converter o SLA: {e}")
        return timedelta(0)

# Função para calcular o SLA
def calcular_sla(datainiciotarefa, fimdatarefa, pausas_str, retomartarefa_str, sla):
    # Ajuste o formato para incluir frações de segundo
    format_str = '%Y-%m-%d %H:%M:%S.%f'
    
    # Verificar se pausas_str e retomartarefa_str são None e inicializar como listas vazias
    pausas_str = pausas_str or ""
    retomartarefa_str = retomartarefa_str or ""
    
    # Converter strings de pausas e retomadas para listas de datetime
    try:
        pausas = [datetime.strptime(p, format_str) for p in pausas_str.split(',') if p]
        retomartarefa = [datetime.strptime(r, format_str) for r in retomartarefa_str.split(',') if r]
    except ValueError as e:
        print(f"Erro ao converter as datas: {e}")
        return timedelta(0), False
    
    # Verifique se pausas e retomadas estão vazias
    if not pausas or not retomartarefa:
        tempo_total_pausas = timedelta(0)
    else:
        # Passo 2: Calcular o tempo total das pausas
        tempo_total_pausas = timedelta(0)
        for pausa, retomar in zip(pausas, retomartarefa):
            tempo_total_pausas += retomar - pausa
    
    # Passo 1: Calcular o tempo total da tarefa
    tempo_total = fimdatarefa - datainiciotarefa
    
    # Passo 3: Calcular o tempo efetivo de trabalho
    tempo_efetivo = tempo_total - tempo_total_pausas
    
    # Passo 4: Comparar com o SLA
    sla_atingido = tempo_efetivo <= sla
    
    return tempo_efetivo, sla_atingido


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

idf = st.sidebar.multiselect("IDs de Tarefas para Filtro", options=tarefas(), format_func=lambda x: str(x[0]), key='KIDF')

if idf:
    pausas = [item[2] for item in idf if len(item) > 2 and item[2] is not None and item[2] != '']
    retomadas = [item[3] for item in idf if len(item) > 3 and item[3] is not None and item[3] != '']
    idf = [str(item[0]) for item in idf]
    if not pausas:
        pausas = []

    if not retomadas:
        retomadas = []    

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
  
image = Image.open("C:/Users/Dux/Desktop/Codando/Projetos/Tarefas/tarefas.webp")

collll1, collll2 = st.columns([7,1])

with collll1:
    #st.markdown("<h1>Atividades</h1>", unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: left; color: white;'>✅ Atividades</h1>", unsafe_allow_html=True)

     

    id_tarefa = st.text_input("Id Tarefa", value='',label_visibility="visible", disabled=True, key='KID')

    status = st.selectbox("Status", ['','Aberto','Pausado','Em Execução'], disabled=False, key='STAT')

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

    realizada = st.text_area("Atividade Realizada", height=50, disabled=False, key='ATR')    

    cliente = st.selectbox("Cliente", [["", ""]] + Cliente(), format_func=lambda x: x[0] if x[0] else "Selecione um cliente", disabled=False, key='KCLI')
    cliente_id = cliente[1] if cliente[0] else None

    cliente_id_invisivel = cliente_id #ATENÇÃO

    col_data, col_hora = st.columns([1, 1])
    with col_data:
        dt_tarefa = st.date_input("Dt. Tarefa", value=None, disabled=False, key='KDTT')
    with col_hora:
        hr_tarefa = st.time_input("Hora Tarefa", value=None, disabled=False, key='KHR')

    col_satis, col_moti = st.columns([0.5,0.5])
    with col_satis:
        satisfacao = st.selectbox("Satisfação", ['','5 - Muito satisfeito', '4 - Parcialmente satisfeito', '3 - Nem satisfeito, Nem insatisfeito', '2 - Parcialmente insatisfeito', '1 - Muito insatisfeito'], disabled=False, key='SATIS')
        motivo = st.selectbox("Motivo", ['','1 - Valor','2 - Teste','3 - Suporte ao Sistema','4 - Funções no Sistema','5 - Outros'], disabled=False, key='MOTI')
   
    observacao = st.text_area("Observação", height=50, disabled=False, key='OBS')   

    colll1, colll2, colll3, colll4 = st.columns([1, 1, 1, 2])
    with colll1:
         if st.button("Iniciar Tarefa"):
             iniciar_tarefa()

    with colll2:
         if st.button("Pausar Tarefa"):
            pausar_tarefa()

    with colll3:
         if st.button("Retomar Tarefa"):
            retomar_tarefa()

    with colll4:
         if st.button("Finalizar Tarefa"):
            finalizar_tarefa()                           

    col1, col2= st.columns([1, 0.63])
    with col1:
        if st.button("Gravar Alterações", disabled=False):
            if hr_tarefa:
                dt_tarefa_completa = datetime.combine(dt_tarefa, hr_tarefa)
                dt_tarefa_formatada = dt_tarefa_completa.strftime("%Y-%m-%d %H:%M:%S.000")
                dt_tarefa_formatada3 = formatar_data_para_sql(dt_tarefa_formatada)
                dt_tarefa_formatada = dt_tarefa_formatada3
            else:
                dt_tarefa_formatada = None  
         
            if validar_campos(status,prioridade, atividade, tarefa, sistema_id, sistema, dt_versao, realizada, cliente_id, cliente, dt_tarefa_formatada):
                gravar_tarefa(status,prioridade, atividade, tarefa, sistema_id, sistema, dt_versao,realizada,cliente_id, cliente, dt_tarefa_formatada,satisfacao,motivo,observacao,id_tarefa,)

    with col2:
        if st.button("Excluir Tarefa", disabled=False):
            excluir_tarefa(id_tarefa)

    

with collll2:    
    st.image(image, width=200)