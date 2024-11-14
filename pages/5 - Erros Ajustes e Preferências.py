import pyodbc
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, time, timedelta
import pandas as pd
from PIL import Image
import io  # Importação do módulo io para manipulação de bytes
import base64
 
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

def erros():
    results = []
    Tar = f"""Select id_erro as id, erro as erro, tipo as tipo, sistema as software, solucao as solucao , Imagem as imagem from erros"""
    cursor.execute(Tar)
    dados = cursor.fetchall()
    #return [item[0] for item in dados]
    for row in dados:
        results.append(list(row))
    return results

def erros2():
    results = []
    Tar = f""" Select tipo as tipo from erros group by tipo order by tipo"""
    cursor.execute(Tar)
    dados = cursor.fetchall()
    #return [item[0] for item in dados]
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
    st.session_state['IDE'] = ''
    st.session_state['ERR'] = ''
    st.session_state['SOFTE'] = ["", ""]
    st.session_state['SOL'] = ''
    st.session_state['EIDF'] = []
    st.session_state['SOFTF'] = []
    st.session_state['IMG_BYTES'] = ''
    st.session_state['TIP'] = ''
    st.session_state['TIPF'] = []


# Função para adicionar erro e imagem ao banco de dados
def adicionar_erro(erro, tipo, sistema_id, sistema, solucao, imagem, definicao):
    if not erro or not sistema_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    img_bytes = pyodbc.Binary(imagem) if imagem is not None else None

    comando = """INSERT INTO erros (erro, tipo, id_sys, sistema, solucao, Imagem, solucaodef) 
                 VALUES (?, ?, ?, ?, ?, ?)"""
    
    parametros = (erro, tipo, sistema_id, sistema_str, solucao, img_bytes, definicao)

    try:
        cursor.execute(comando, parametros)
        conexao.commit()
        st.success('Erro adicionado com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao gravar no banco de dados: {e}')

def gravar_erro(erro, tipo,sistema_id, sistema, solucao, imagem, definicao, id_erro):
    if not id_erro or not erro or not sistema_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    sistema_str = sistema[0] if isinstance(sistema, tuple) else sistema
    #img_bytes = pyodbc.Binary(imagem) if imagem is not None else None
    #img_bytes = pyodbc.Binary(st.session_state.get('IMG_BYTES')) if st.session_state.get('IMG_BYTES') is not None else None
    img_bytes = pyodbc.Binary(imagem) if imagem is not None else (pyodbc.Binary(st.session_state.get('IMG_BYTES')) if st.session_state.get('IMG_BYTES') is not None else None)
    
    id_erro = int(id_erro) 
    
    comando = """UPDATE erros 
                 SET  erro = ?, tipo = ?, id_sys = ?, sistema = ?, solucao = ?, Imagem = ?, solucaodef = ?
                 WHERE id_erro = ?"""
    
    parametros = (erro, tipo, sistema_id, sistema_str, solucao, img_bytes, definicao, id_erro) 

    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Erro gravada com sucesso')
        
    except pyodbc.Error as e:
        st.error(f'Erro ao atualizar no banco de dados: {e}')    

def excluir_erro(id_erro):
    if not id_erro or not erro or not sistema_id:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    id_erro = int(id_erro)
    
    comando = """DELETE FROM erros WHERE id_erro =?"""
    
    parametros = (id_erro)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Erro excluida com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao excluir no banco de dados: {e}')         

def validar_campos(erro, sistema_id, sistema, solucao):
    if not erro:
        st.error("Erro é obrigatória.")
        return False
    if not sistema_id:
        st.error("Prioridade é obrigatória.")
        return False
    if not sistema:
        st.error("Sistema é obrigatória.")
        return False
    if not solucao:
        st.error("Solução é obrigatória.")
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
    
def buscar_tarefas_filtradas_multiplos_filtros_com_data(erros_ids=None, soft_ids=None, tip_ids=None):
    if not erros_ids and not soft_ids and not tip_ids:
        return [], []

    condicoes = []
    parametros = []

    if erros_ids:
        placeholders_erros = ', '.join('?' for _ in erros_ids)
        condicoes.append(f"t.id_erro IN ({placeholders_erros})")
        parametros.extend(erros_ids)

    if soft_ids:
        placeholders_soft = ', '.join('?' for _ in soft_ids)
        condicoes.append(f"t.id_sys IN ({placeholders_soft})")
        parametros.extend(soft_ids)

    if tip_ids:
        placeholders_tip = ', '.join('?' for _ in tip_ids)
        condicoes.append(f"t.tipo IN ({placeholders_tip})")
        parametros.extend(tip_ids)    

    condicao_final = ' AND '.join(condicoes)

    comando = f"""
    SELECT
        t.id_erro AS 'ID',
        t.erro as 'Erro',
        t.tipo as 'Tipo',
        s.software AS 'Software/Módulo',
        t.solucao AS 'Solução',
        t.Imagem as 'Foto',
        t.solucaodef as 'Solução Definitiva?'
    FROM
        erros t
    JOIN
        softwares s ON t.id_sys = s.id_soft
    """
    
    if condicoes:
        comando += f" WHERE {condicao_final}"   

    cursor.execute(comando, parametros)
    dados = cursor.fetchall()

    colunas = ['ID','Erro','Tipo','Software/Módulo', 'Solução', 'Foto', 'Solu. Definitiva?']
    tarefas = [list(item) for item in dados]
    
    return tarefas, colunas

def format_date(date):
    return date.strftime('%d/%m/%Y') 

# Função para converter bytes para imagem
def bytes_to_image(foto_bytes):
    try:
        if isinstance(foto_bytes, bytes):
            return Image.open(io.BytesIO(foto_bytes))
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao abrir imagem: {e}")
        return None

# Função para redimensionar a imagem (você já deve ter isso implementado)
def redimensionar_imagem(img, largura=100):
    return img.resize((largura, int(largura * img.height / img.width)))

# Função para converter a imagem para HTML com base64
def imagem_para_html(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_b64}" width="100"/>'

def exibir_dataframe_com_botoes(df, col1, col2):
    # Lista para armazenar imagens miniatura
    miniaturas_html = []
    
    for index, row in df.iterrows():
        # Converte os bytes da foto
        foto_bytes = row.get('Foto', '')
        img = bytes_to_image(foto_bytes) if foto_bytes else None
        
        if img:
            img_miniatura = redimensionar_imagem(img)  # Redimensiona a imagem
            img_html = imagem_para_html(img_miniatura)
            miniaturas_html.append(img_html)
        else:
            miniaturas_html.append('')  # Adiciona uma célula vazia se não houver imagem

    # Adiciona as miniaturas de imagem ao DataFrame
    df['Foto'] = miniaturas_html

    st.dataframe(df,
             column_config={
                "Foto": st.column_config.ImageColumn(),
             })

    # Exibe o DataFrame na coluna 1
    with col1:
        st.write(df[['ID', 'Erro', 'Tipo', 'Software/Módulo', 'Solução','Foto']])
    
    # Exibe a imagem na coluna 2
    with col2:
        for img_html in miniaturas_html:
            st.markdown(img_html, unsafe_allow_html=True)
          
def exibir_dataframe_com_session_state(df, col1, col2):
    global imagem_binaria1
    for index, row in df.iterrows():
        id_value = row.get('ID', '')
        st.session_state['IDE'] = str(id_value)    
        st.session_state['ERR'] = row.get('Erro', '')
        st.session_state['TIP'] = row.get('Tipo', '')
        st.session_state['SOL'] = row.get('Solução', '') 

        software_modulo = row.get('Software/Módulo', '')
        sistemas_opcoes = Sistemas()  # Assumindo que Sistemas() retorna uma lista de opções
        for sistema in sistemas_opcoes:
            if software_modulo == sistema[0]:
                st.session_state['SOFTE'] = sistema
                break
        else:
            st.session_state['SOFTE'] = sistemas_opcoes[0]

        # Converte a imagem de bytes
        foto_bytes = row.get('Foto', None)  # Corrigido para usar None como fallback
        

        if foto_bytes is None or foto_bytes == '' or foto_bytes == b'' or foto_bytes == 'b''':  # Verifica se foto_bytes é None ou vazio
           st.session_state['IMG_BYTES'] = None
           imagem = None  # Define imagem como None se não houver dados
        else:
           st.session_state['IMG_BYTES'] = foto_bytes
           imagem_binaria1 = foto_bytes
           imagem = bytes_to_image(foto_bytes)  # Converte os bytes para imagem

        with col2:
            if imagem:
                st.image(imagem, caption=f"Foto ID: {st.session_state['IDE']}", use_column_width=True)
            else:
                st.write("Sem imagem disponível")  # Mensagem caso não haja imagem

def app(uploaded_file):
    if uploaded_file is not None:
        img_bytes = uploaded_file.read()  # Lê a imagem como binário
        st.image(Image.open(uploaded_file), caption="Imagem Selecionada", use_column_width=True)
        st.write("Imagem armazenada com sucesso na variável.")
        return img_bytes  # Retorna a imagem em bytes
    return None

# Função para converter dados binários em URL base64
def converter_para_base64(dados_binarios):
    # Converter dados binários em base64
    base64_img = base64.b64encode(dados_binarios).decode('utf-8')
    # Adicionar o prefixo necessário para o tipo de imagem (assumindo PNG aqui)
    return f"data:image/png;base64,{base64_img}"


# Processando e exibindo os resultados da consulta
def processar_resultados_com_imagem(tarefas, colunas):
    dados_jogadores = []
    for row in tarefas:
        ide = row[0]
        erro1 = row[1]  # Supondo que a coluna 1 seja 'Erro'
        tipo1 = row[2]
        Software1 = row[3]
        solucao1 = row[4]
        definicao1 = row[6]
        imagem_base64 = converter_para_base64(row[5]) if row[5] else None  # Coluna 4 é 'Foto'
        dados_jogadores.append({'ID': ide,'Erro': erro1,'Tipo': tipo1,'Software': Software1,'Solucao': solucao1, 'Foto Erro': imagem_base64, 'Solu. Definitiva?': definicao1})

    df_jogadores = pd.DataFrame(dados_jogadores)
    
    # Exibindo o DataFrame no Streamlit
    st.dataframe(df_jogadores, column_config={
        "Foto Erro": st.column_config.ImageColumn("Foto Erro")  # Exibição da imagem no DataFrame
    })

# Inicializando st.session_state para os checkboxes, se ainda não existir
if 'Csim' not in st.session_state:
    st.session_state['Csim'] = True  # Inicia selecionado

if 'Cnao' not in st.session_state:
    st.session_state['Cnao'] = False  # Inicia desmarcado    

# Função para lidar com a alternância dos checkboxes
def toggle_checkboxes(selected):
    if selected == 'Csim':
        st.session_state['Csim'] = True
        st.session_state['Cnao'] = False
        st.session_state['solucao'] = 'Sim'  # Atribui "Sim" à variável
    elif selected == 'Cnao':
        st.session_state['Csim'] = False
        st.session_state['Cnao'] = True
        st.session_state['solucao'] = 'Não'  # Atribui "Não" à variável

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

alterar_disabled = True   
idf = st.sidebar.multiselect("IDs de Erros para Filtro", options=erros(), format_func=lambda x: str(x[0]), key='EIDF')
softf = st.sidebar.multiselect("Software para Filtro", options=Sistemas(), format_func=lambda x: x[0], key='SOFTF')
tipf = st.sidebar.multiselect("Tipos para Filtro", options=erros2(), format_func=lambda x: x[0], key='TIPF')

colll1, colll2 = st.columns([1,0.5])
with colll2:  
    uploaded_file = st.file_uploader("Escolha uma imagem", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        # Processar a imagem e armazenar
        imagem_binaria = app(uploaded_file)
        st.session_state['IMG_BYTES'] = imagem_binaria
            
with colll1:
  
  if idf:
    idf = [str(item[0]) for item in idf]

  if idf and not softf and not tipf:
    id_filtro = idf if idf else None 
    tarefas_filtradas2, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(erros_ids=idf)
    if tarefas_filtradas2:
      st.write("Filtro carregado:")
      processar_resultados_com_imagem(tarefas_filtradas2, colunas)#pd.DataFrame(tarefas_filtradas2, columns=colunas)
      df_tarefas2 = pd.DataFrame(tarefas_filtradas2, columns=colunas)
      if df_tarefas2.shape[0] == 1:
            alterar_disabled = False 
            df = df_tarefas2
      else:
            alterar_disabled = True
    else: 
      if softf and idf and tipf:
        id_filtro = []
  else: 
    id_filtro = []        

  if softf and not idf and not tipf:
    soft_ids_filtro = [soft[1] for soft in softf]
    tarefas_filtradas, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(soft_ids=soft_ids_filtro)
    if tarefas_filtradas:
        st.write("Filtro carregado:")
        processar_resultados_com_imagem(tarefas_filtradas, colunas)
        df_tarefas3 = pd.DataFrame(tarefas_filtradas, columns=colunas)
        if df_tarefas3.shape[0] == 1:
            alterar_disabled = False  
            df = df_tarefas3
        else:
            alterar_disabled = True
    else:
       if softf and idf and tipf: 
          soft_ids_filtro = []
  else:
    soft_ids_filtro = []

  if tipf and not softf and not idf:
    tip_ids_filtro = [tip[0] for tip in tipf]
    tarefas_filtradas4, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(tip_ids=tip_ids_filtro)
    if tarefas_filtradas4:
        st.write("Filtro carregado:")
        processar_resultados_com_imagem(tarefas_filtradas4, colunas)
        df_tarefas4 = pd.DataFrame(tarefas_filtradas4, columns=colunas)
        if df_tarefas4.shape[0] == 1:
            alterar_disabled = False  
            df = df_tarefas4
        else:
            alterar_disabled = True
    else:
       if softf and idf and tipf: 
        tip_ids_filtro = []
  else:
    tip_ids_filtro = []  

  if softf and idf:
    soft_ids_filtro = [soft[1] for soft in softf]
    id_filtro = idf if idf else None 
    tarefas_filtradas3, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(erros_ids=idf,soft_ids=soft_ids_filtro)
    if tarefas_filtradas3:
        st.write("Filtro carregado:")
        processar_resultados_com_imagem(tarefas_filtradas3, colunas)
        df_tarefas4 = pd.DataFrame(tarefas_filtradas3, columns=colunas)
        if df_tarefas4.shape[0] == 1:
            alterar_disabled = False  
            df = df_tarefas4
        else:
            alterar_disabled = True
    else:
       if softf and idf: 
        soft_ids_filtro = []
        id_filtro = []
  else:
    soft_ids_filtro = []  
    id_filtro = []

  if tipf and idf:
    tip_ids_filtro = [tip[0] for tip in tipf]
    id_filtro = idf if idf else None 
    tarefas_filtradas5, colunas = buscar_tarefas_filtradas_multiplos_filtros_com_data(erros_ids=idf,tip_ids=tip_ids_filtro)
    if tarefas_filtradas5:
        st.write("Filtro carregado:")
        processar_resultados_com_imagem(tarefas_filtradas5, colunas)
        df_tarefas5 = pd.DataFrame(tarefas_filtradas5, columns=colunas)
        if df_tarefas5.shape[0] == 1:
            alterar_disabled = False  
            df = df_tarefas5
        else:
            alterar_disabled = True
    else:
       if tipf and idf: 
        tip_ids_filtro = []
        id_filtro = []
  else:
    tip_ids_filtro = []
    id_filtro = []  
    

  if st.sidebar.button("Alterar", disabled=alterar_disabled):
    #exibir_dataframe_com_session_state(st.session_state.get('df', pd.DataFrame()),colll1, colll2) 
    exibir_dataframe_com_session_state(df,colll1, colll2)

  st.markdown("<h1 style='text-align: left; color: white;'>🔧 Erros/Ajustes e Preferências</h1>", unsafe_allow_html=True)

  id_erro = st.text_input("Id Erro", value='', label_visibility="visible", disabled=True, key='IDE')
  tipo = st.selectbox("Tipo", ['', 'Erro', 'Ajuste', 'Funções'], disabled=False, key='TIP', )
  erro = st.text_area("Erro/Ajuste ou Preferência", height=50, disabled=False, key='ERR')
  sistema = st.selectbox("Software/Módulo", [["", ""]] + Sistemas(), format_func=lambda x: x[0] if x[0] else "Selecione um Software", disabled=False, key='SOFTE')
  solucao = st.text_area("Solução", height=50, disabled=False, key='SOL')
  sistema_id = sistema[1] if sistema[0] else None 

  st.text('Solução Definitiva?')
  # Checkbox "Sim"
  st.checkbox('Sim', key='Csim', on_change=toggle_checkboxes, args=('Csim',))

  # Checkbox "Não"
  st.checkbox('Não', key='Cnao', on_change=toggle_checkboxes, args=('Cnao',)) 

  if st.session_state['Csim']:
      definicao = 'Sim'

  if st.session_state['Cnao']:
      definicao = 'Não'    

      
  col1, col2, col3= st.columns([1, 1, 1.5])
  with col1:
        if st.button("Adicionar Tarefa"):
            if validar_campos(erro, sistema_id, sistema, solucao):
                adicionar_erro(erro, tipo, sistema_id, sistema, solucao, imagem_binaria, definicao)

  with col2:
        if st.button("Gravar Alterações", disabled=False):
            if st.session_state['IMG_BYTES'] is None:
               imagem_binaria = imagem_binaria1
            else:
               imagem_binaria = st.session_state['IMG_BYTES']  

            if validar_campos(erro, sistema_id, sistema, solucao):
                gravar_erro(erro, tipo, sistema_id, sistema, solucao, imagem_binaria, definicao, id_erro)  
                  
  with col3:
    if st.button("Excluir Tarefa", disabled=False):
        excluir_erro(id_erro)   

 

      

    

          

        