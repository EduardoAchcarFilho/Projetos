import pyodbc
import streamlit as st
import json
from streamlit_calendar import calendar
from datetime import datetime


# Configurações de conexão
dados_conexao = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=tasks;"
    "Trusted_Connection=yes;"
)
conexao = pyodbc.connect(dados_conexao)
cursor = conexao.cursor()

# Função para carregar eventos do banco de dados
def carregar_eventos():
    cursor.execute("""
        SELECT id_task, tarefa, cliente, Prioridade, dt_tarefa 
        FROM tarefas 
        WHERE status <> 'Finalizada' 
        AND Prioridade IS NOT NULL 
    """)
    eventos = []
    for row in cursor.fetchall():
        eventos.append({
            "id": row.id_task,
            "title": f"{row.id_task} | {row.tarefa} | {row.cliente} | {row.Prioridade}",
            "start": row.dt_tarefa.strftime("%Y-%m-%dT%H:%M:%S"),
            "backgroundColor": "#FF4B4B" if row.Prioridade == 'ALTO' else "#3D9DF3" if row.Prioridade == 'MEDIO' else "#3DD56D",
            "borderColor": "#FF4B4B" if row.Prioridade == 'ALTO' else "#3D9DF3" if row.Prioridade == 'MEDIO' else "#3DD56D",
            "allDay": False
        })
    return eventos

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

# Função para atualizar um evento no banco de dados
def atualizar_evento(id_task, novo_inicio):
    try:
        novo_inicio_formatado = formatar_data_para_sql(novo_inicio)
        
        if novo_inicio_formatado is None:
            return
        
        cursor.execute("""
            UPDATE tarefas 
            SET dt_tarefa = ? 
            WHERE id_task = ?
        """, novo_inicio_formatado, id_task)
        conexao.commit()
    except Exception as e:
        print(f"Erro ao atualizar o evento {id_task}: {str(e)}")

# Carregar os eventos do banco de dados ao iniciar
eventos = carregar_eventos()

# Obter a data atual
hoje = datetime.now()
primeiro_dia_do_mes = hoje.replace(day=1).date()

# Configurações do Streamlit
st.set_page_config(page_title="Calendário Tarefas EdX", page_icon="📆", layout="wide")

# Legenda no sidebar
st.sidebar.title("Legenda de Prioridades")

# Adicionando a legenda com as bolinhas coloridas usando Markdown
st.sidebar.markdown("""
    <div style="display: flex; align-items: center;">
        <span style="color: red; font-size: 24px;">&#9679;</span>&nbsp;ALTO
    </div>
    <div style="display: flex; align-items: center;">
        <span style="color: blue; font-size: 24px;">&#9679;</span>&nbsp;MEDIO
    </div>
    <div style="display: flex; align-items: center;">
        <span style="color: green; font-size: 24px;">&#9679;</span>&nbsp;BAIXO
    </div>
    """, unsafe_allow_html=True)

# Adicionando a data e a hora no sidebar
current_date = datetime.now().strftime('%d/%m/%Y')
current_time = datetime.now().strftime('%H:%M')

st.sidebar.markdown("""---""")

# Usando HTML para colocar a data e a hora lado a lado
st.sidebar.markdown(f"""
    <div style="display: flex; justify-content: space-between;">
        <div><strong>Data:</strong> {current_date}</div>
        <div><strong>Hora:</strong> {current_time}</div>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("""---""")

st.sidebar.button("📧 Enviar Confirmações por Email")

st.sidebar.button("📱 Enviar Confirmações por Whatsapp")

st.markdown("<h1 style='text-align: center; color: white;'>📅 Calendário - TaskEdx</h1>", unsafe_allow_html=True)

mode = st.selectbox(
        "Modelo calendário",
        (
            "Mensal",
            "Semanal-Hora",
            "Mensal-Timeline",
            "Mês-Lista",
            "Anual",
        ),
    )

calendar_options = {
        "editable": True,
        "navLinks": True,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": f"{mode},dayGridWeek,dayGridDay",
        },
        "initialDate": f"{datetime.now().replace(day=1).date()}",
        "initialView": mode,
        "weekNumbers": False,
        "height": "auto",
        "contentHeight": "auto",
        "aspectRatio": 1.8,
    }

if mode == "Mensal":
        calendar_options = {
            **calendar_options,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridDay,dayGridWeek,dayGridMonth",
            },
            "initialDate": f"{primeiro_dia_do_mes}",
            "initialView": "dayGridMonth",
        }
elif mode == "Semanal-Hora":
        calendar_options = {
            **calendar_options,
            "initialDate": f"{datetime.now().date()}",  # Define a data atual
            "initialView": "timeGridWeek",
        }
elif mode == "Mensal-Timeline":
        calendar_options = {
            **calendar_options,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "timelineDay,timelineWeek,timelineMonth",
            },
            "initialDate": f"{primeiro_dia_do_mes}",
            "initialView": "timelineMonth",
        }
elif mode == "Mês-Lista":
        calendar_options = {
            **calendar_options,
            "initialDate": f"{primeiro_dia_do_mes}",
            "initialView": "listMonth",
        }
elif mode == "Anual":
        calendar_options = {
            **calendar_options,
            "initialView": "multiMonthYear",
        }

state = calendar(
        events=eventos,
        options=calendar_options,
        key=mode,
    )

if state:
        if "eventChange" in state:
            event_change_data = state["eventChange"]
            old_event = event_change_data.get("oldEvent", {})
            new_event = event_change_data.get("event", {})

            event_id = new_event.get("id")
            novo_inicio = new_event.get("start")

            if event_id and novo_inicio:
                atualizar_evento(event_id, novo_inicio)
            else:
                st.error("ID do evento ou nova data não encontrados.")    