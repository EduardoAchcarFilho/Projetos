import pyodbc
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, time
import pandas as pd
import folium
from streamlit_folium import st_folium
from opencage.geocoder import OpenCageGeocode
from PIL import Image
 
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connections=yes;"
)

conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

def Cliente():
    results = []
    Clii1 = f"""Select id_cli as id ,nome as nome from clientes"""
    cursor.execute(Clii1)
    dados = cursor.fetchall()
    for row in dados:
        results.append(list(row))
    return results

def filtrar_dados(dataframe, colunas_selecionadas):
    if colunas_selecionadas:
        dataframe = dataframe[colunas_selecionadas]
    return dataframe

def limpar_inputs():
    st.session_state['IDCLI'] = ''
    st.session_state['NCLI'] = ''
    st.session_state['END'] = ''
    st.session_state['NUM'] = ''
    st.session_state['BAI'] = ''
    st.session_state['CID'] = ''
    st.session_state['SEG'] = ''
    st.session_state['CEL'] = ''
    st.session_state['EMAIL'] = ''
    st.session_state['MEIO'] = ''
    st.session_state['TEL'] = ''
    st.session_state['IDF'] = []
    st.session_state['CLIF'] = []
    st.session_state.endereco = ""
    st.session_state.numero = ""
    st.session_state.bairro = ""
    st.session_state.cidade = ""
    
def adicionar_cliente(nome,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone):
    if not nome:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    cliente_str = nome[0] if isinstance(nome, list) else nome
    
    comando = """INSERT INTO clientes (Nome, Ende, Numero, Bairro, Cidade, Seque, Cel, Email, Meio_Comuni, Tel) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    
    parametros = (cliente_str,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone)

    print(comando)
    print(parametros)
    
    try:
        cursor.execute(comando, parametros)
        conexao.commit()
        st.success('Cliente adicionado com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao gravar no banco de dados: {e}')

def gravar_cliente(id_cliente,nome,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone):
    if not id_cliente or not nome:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    cliente_str = nome[0] if isinstance(nome, list) else nome
    id_cliente = int(id_cliente)
    
    comando = """UPDATE clientes 
                 SET Nome = ?, Ende = ?, Numero = ?, Bairro = ?, Cidade = ?, Seque = ?, Cel = ?, Email = ?, Meio_Comuni = ?, 
                     Tel = ?
                 WHERE id_cli = ?"""
    
    parametros = (cliente_str,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone,id_cliente)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Cliente Atualizado com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao atualizar no banco de dados: {e}')   

def excluir_tarefa(id_cliente):
    if not id_cliente:
        st.error('Campos vazios ou inválidos, operação não realizada')
        return
    
    id_cliente = int(id_cliente)
    
    comando = """DELETE FROM clientes WHERE id_cli =?"""
    
    parametros = (id_cliente)
    
    try:
        cursor.execute(comando, parametros)  
        conexao.commit()
        st.success('Tarefa excluida com sucesso')
    except pyodbc.Error as e:
        st.error(f'Erro ao excluir no banco de dados: {e}')     

def validar_campos(nome,endereco,seguemento,celular,email,meio,telefone):
    if not nome:
        st.error("Nome é obrigatória.")
        return False
    if not endereco:
        st.error("Endereço é obrigatória.")
        return False
    if not seguemento:
        st.error("Segmento é obrigatória.")
        return False
    if not celular:
        st.error("Celular é obrigatório.")
        return False
    #if not email:
    #    st.error("Email é obrigatório.")
    #    return False
    #if not meio:
    #    st.error("Meio Comunicação é obrigatória.")
    #    return False
    #if not telefone:
    #    st.error("Telefone é obrigatório.")
    #    return False
    return True     

def buscar_cliente_filtros(cliente_ids=None,cliente_str=None):
    if not cliente_ids and not cliente_str:
        return [], []

    condicoes = []
    parametros = []

    if cliente_ids:
        placeholders_idcliente = ', '.join('?' for _ in cliente_ids)
        condicoes.append(f"t.id_cli IN ({placeholders_idcliente})")
        parametros.extend(cliente_ids)

    if cliente_str:
        placeholders_cliente = ', '.join('?' for _ in cliente_str)
        condicoes.append(f"t.Nome IN ({placeholders_cliente})")
        parametros.extend(cliente_str)    

    condicao_final = ' AND '.join(condicoes)

    comando = f"""
    SELECT 
      t.id_cli as ID,       
      t.Nome as Nome,       
      t.Ende as Endereço,
      t.Numero as Numero,
      t.Bairro as Bairro,
      t.Cidade as Cidade,   
      t.Seque as Segmento,
      t.Cel as Celular,      
      t.Email as Email,      
      t.Meio_Comuni as Meio,
      t.Tel as Telefone
    FROM 
       clientes t
    """
    
    if condicoes:
        comando += f" WHERE {condicao_final}"   

    cursor.execute(comando, parametros)
    dados = cursor.fetchall()

    colunas = ['ID', 'Nome','Endereço','Numero','Bairro','Cidade','Segmento','Celular','Email','Meio','Telefone']
    tarefas = [list(item) for item in dados]
    
    return tarefas, colunas    

def exibir_dataframe_com_botoes(df):
    for index, row in df.iterrows():
    
        df = pd.DataFrame({
        'ID': [row.get('ID', '')],
        'Nome': [row.get('Nome', '')],
        'Endereço':[row.get('Endereço', '')],
        'Numero':[row.get('Numero', '')],
        'Bairro':[row.get('Bairro', '')],
        'Cidade':[row.get('Cidade', '')],
        'Segmento':[row.get('Segmento', '')],
        'Celular':[row.get('Celular', '')],
        'Email':[row.get('Email', '')],
        'Meio':[row.get('Meio', '')],
        'Telefone':[row.get('Telefone', '')],                   
        })
        st.session_state['df'] = df

def exibir_dataframe_com_session_state(df):
    for index, row in df.iterrows():

        id_value = row.get('ID', '')
        st.session_state['IDCLI'] = str(id_value) 
        st.session_state['NCLI'] = row.get('Nome', '')
        st.session_state['END'] = row.get('Endereço', '')
        st.session_state['NUM'] = row.get('Numero', '')
        st.session_state['BAI'] = row.get('Bairro', '')
        st.session_state['CID'] = row.get('Cidade', '')
        st.session_state['SEG'] = row.get('Segmento', '')
        st.session_state['CEL'] = row.get('Celular', '')
        st.session_state['EMAIL'] = row.get('Email', '')
        st.session_state['MEIO'] = row.get('Meio', '')
        st.session_state['TEL'] = row.get('Telefone', '')

# Injetando CSS para ajustar o tamanho dos inputs
st.markdown(
    """
    <style>
    .stTextInput {
        width: 85% !important;  /* Ajuste a largura como desejar */
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
    .ID {
        .stTextInput {
        width: 30% !important;  /* Ajuste a largura como desejar */
    }   
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<h1 class="titulo2">Filtros</h1>', unsafe_allow_html=True)

if st.sidebar.button('Limpar'):
    limpar_inputs() 

alterar_disabled = True   
ids = st.sidebar.multiselect("IDs dos Clientes para Filtro", options=Cliente(), format_func=lambda x: str(x[0]), key='IDF')
Clif = st.sidebar.multiselect("Cliente para Filtro", options=Cliente(), format_func=lambda x: x[1], key='CLIF')  

if ids and not Clif:
    id_filtro = [id[0] for id in ids]
    tarefas_filtradas2, colunas = buscar_cliente_filtros(cliente_ids=id_filtro)
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
      if Clif and ids:
        id_filtro = []
else: 
    id_filtro = []   

if Clif and not ids:
    Soft_filtro = [item[1] for item in Clif] if Clif else None
    tarefas_filtradas2, colunas = buscar_cliente_filtros(cliente_str=Soft_filtro)
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
      if Clif and ids:
        Soft_filtro = []
else: 
    Soft_filtro = [] 

# Use sua chave de API do OpenCage
API_KEY = '2905eadfb9e74297b9be1bff10250306'
geocoder = OpenCageGeocode(API_KEY)

# Coordenadas para Praia Grande, São Paulo, Brazil
praia_grande_coords = [-24.0057, -46.4029]  # Latitude e longitude de Praia Grande

# Criar o mapa com Folium
m = folium.Map(location=praia_grande_coords, zoom_start=12)  # Posição inicial em Praia Grande, São Paulo

# Inicializar st.session_state se não estiver já inicializado
if 'endereco' not in st.session_state:
    st.session_state.endereco = ""
    st.session_state.numero = ""
    st.session_state.bairro = ""
    st.session_state.cidade = ""
    st.session_state.estado = ""
    st.session_state.pais = ""    

colll1, colll2 = st.columns([0.5,0.5])

with colll1:
  if st.sidebar.button("Alterar", disabled=alterar_disabled):
      exibir_dataframe_com_session_state(st.session_state.get('df', pd.DataFrame()))          

  #st.markdown('<h1 class="titulo2">Cadastro - Clientes</h1>', unsafe_allow_html=True)
  image = Image.open("C:/Users/Dux/Desktop/Codando/Projetos/Tarefas/clientes.webp")

  #st.markdown("""
  #  <div style="display: flex; align-items: left;">
  ##  <h1 class="titulo2">Cadastro - Clientes</h1>
  #  </div>
  #  """, unsafe_allow_html=True)
  
  st.markdown("<h1 style='text-align: left; color: white;'>👥 Cadastro - Clientes</h1>", unsafe_allow_html=True)

  #st.image(image, width=50)
 
  colu, colu2, colu3 = st.columns([0.5,0.5,0.5])

  with colu:
   id_cliente = st.text_input("Id Cliente", value='',label_visibility="visible", disabled=True, key='IDCLI')

  nome = st.text_input("Cliente", value='',label_visibility="visible", disabled=False, key='NCLI') 

  endereco = st.text_input("Endereço", value=st.session_state.endereco, label_visibility="visible", disabled=False, key='END')

  numero = st.text_input("Numero", value=st.session_state.numero, label_visibility="visible", disabled=False, key='NUM')

  bairro = st.text_input("Bairro", value=st.session_state.bairro, label_visibility="visible", disabled=False, key='BAI')

  cidade = st.text_input("Cidade", value=st.session_state.cidade, label_visibility="visible", disabled=False, key='CID')  

  segmento = st.text_input("Segmento", value='',label_visibility="visible", disabled=False, key='SEG')   

  celular = st.text_input("Celular", value='',label_visibility="visible", disabled=False, key='CEL') 

  email = st.text_input("Email", value='',label_visibility="visible", disabled=False, key='EMAIL')  

  meio =  st.selectbox("Meio Contato Preferido", ['','Telefone','Celular','Email','Whatsapp'], disabled=False, key='MEIO')  

  telefone = st.text_input("Telefone", value='',label_visibility="visible", disabled=False, key='TEL') 

  col1, col2, col3= st.columns([1, 1, 1])
  with col1:
        if st.button("Adicionar Tarefa"):
            if validar_campos(nome,endereco,segmento,celular,email,meio,telefone):
                adicionar_cliente(nome,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone)
                

  with col2:
        if st.button("Gravar Alterações", disabled=False):     
            if validar_campos(nome,endereco,segmento,celular,email,meio,telefone):
                gravar_cliente(id_cliente,nome,endereco,numero,bairro,cidade,segmento,celular,email,meio,telefone)
                

  with col3:
    if st.button("Excluir Tarefa", disabled=False):
        excluir_tarefa(id_cliente)
        
with colll2:
    st.markdown('<h1 class="titulo1">Mapa</h1>', unsafe_allow_html=True)
    # Adicionar o mapa ao Streamlit
    output = st_folium(m, width=700, height=500)

    # Função para formatar o endereço no padrão desejado
    def format_address(location):
        components = location[0]['components']
        road = components.get('road', '')
        house_number = components.get('house_number', '')
        suburb = components.get('suburb', '')
        city = components.get('city', '')
        state = components.get('state', '')
        country = components.get('country', '')
        
        # Retornar um dicionário com os componentes do endereço
        formatted_address = {
            "road": road,
            "house_number": house_number,
            "suburb": suburb,
            "city": city,
            "state": state,
            "country": country
        }
        
        return formatted_address

    # Verificar se o usuário clicou no mapa e se 'last_clicked' não é None
    if output and output.get("last_clicked") is not None:
        lat = output["last_clicked"]["lat"]
        lon = output["last_clicked"]["lng"]

        # Exibir as coordenadas capturadas
        #st.write(f"Coordenadas capturadas: Latitude={lat}, Longitude={lon}")

        # Obter o endereço com base nas coordenadas usando OpenCage
        location = geocoder.reverse_geocode(lat, lon)

        # Verificar se a API retornou uma resposta
        if location:
            address_components = format_address(location)
            st.session_state.endereco = address_components.get("road", "")
            st.session_state.numero = address_components.get("house_number", "")
            st.session_state.bairro = address_components.get("suburb", "")
            st.session_state.cidade = address_components.get("city", "")
            st.session_state.estado = address_components.get("state", "")
            st.session_state.pais = address_components.get("country", "")

        else:
            st.write("Nenhum endereço encontrado para essas coordenadas.")
    else:
        st.write("Clique em algum ponto no mapa para obter o endereço.")
