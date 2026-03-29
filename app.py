import streamlit as st
import json
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OmniCharacterAI", page_icon="🌌", layout="wide")

# --- INYECCIÓN DE CSS PARA DARK MODE PREMIUM ---
def inject_custom_css():
    st.markdown("""
        <style>
        /* Fondo principal oscuro y elegante */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        
        /* Ocultar menú de Streamlit y footer para inmersión */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Estilización de los contenedores de chat */
        .stChatMessage {
            background-color: #161b22;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid #30363d;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        /* Avatar transparente para inyectar emojis nativos sin fondo molesto */
        .stChatMessage .st-emotion-cache-1c7y2kd {
            background-color: transparent !important;
            font-size: 1.5rem;
        }
        
        /* Input de chat: estilo glassmorphism oscuro */
        .stChatInputContainer {
            background-color: rgba(22, 27, 34, 0.8) !important;
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid #30363d !important;
            padding-bottom: 2rem;
        }

        /* Botones del Sidebar */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            background-color: #238636;
            color: white;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #2ea043;
            box-shadow: 0 0 10px rgba(46, 160, 67, 0.4);
        }
        
        /* Modificar el selectbox para dark mode */
        div[data-baseweb="select"] > div {
            background-color: #161b22;
            color: #c9d1d9;
            border-color: #30363d;
        }
        </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE PROMPTS Y PERSONALIDAD ---
STYLES = {
    "Flash Fiction": "Responde de forma brutalmente directa, aguda y concisa. Tus respuestas deben tener MÁXIMO 50 palabras. No uses descripciones innecesarias, ve al grano.",
    "Novela Visual": "Mantén un equilibrio perfecto entre diálogo interactivo y descripciones ligeras del entorno. Tu tono debe ser cautivador, emocional y dramático. Haz que los personajes cobren vida.",
    "Épico/Hard-Roleplay": "Escribe prosa literaria extensa y profundamente inmersiva. Incluye monólogos internos complejos, describe texturas, olores y clima, y desarrolla meticulosamente la atmósfera."
}

def get_system_prompt(style, summary):
    base_prompt = (
        f"Eres el Motor Narrativo (Dungeon Master) y los NPCs de esta historia interactiva. El usuario es el protagonista.\n"
        f"Tu estilo estricto es:\n\n"
        f"'{STYLES[style]}'\n\n"
        f"Regla de Oro 1: RESPONDE SIEMPRE Y ÚNICAMENTE EN ESPAÑOL.\n"
        f"Regla de Oro 2: Nunca rompas la inmersión. Jamás menciones que eres una IA.\n"
        f"Regla de Oro 3: Narra el mundo y las reacciones, pero NO hables ni tomes decisiones por el usuario (no uses 'Yo' para narrar sus acciones).\n"
    )
    if summary:
         base_prompt += f"\n[Memoria Omnisciente - Sinopsis de lo ocurrido antes del buffer actual]:\n{summary}\n"
    
    return base_prompt

# --- INICIALIZACIÓN DE ESTADO ---
def init_state():
    if "messages" not in st.session_state:
         st.session_state.messages = []
    if "summary" not in st.session_state:
         st.session_state.summary = ""
    if "buffer_size" not in st.session_state:
         st.session_state.buffer_size = 6  # Recordar los últimos 6 mensajes intercambiados en buffer Inmediato

# --- MOTOR DE RESUMEN RECURSIVO ---
def summarize_old_messages(old_messages, current_summary):
    try:
      llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash", temperature=0.8, google_api_key=st.secrets["GOOGLE_API_KEY"])

      history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in old_messages])

      prompt = (
            "Eres un condensador de memoria omnisciente. Tu tarea es resumir la siguiente porción de historia, "
            "fusionándola orgánicamente con la memoria persistente anterior (si existía) para preservar el contexto vital a largo plazo. "
            "Retén hitos importantes, decisiones clave y motivaciones emocionales de forma concisa. ESCRIBE EL RESUMEN EXCLUSIVAMENTE EN ESPAÑOL.\\n\\n"
            f"[Memoria Persistente Anterior]: {current_summary if current_summary else 'Ninguna'}\\n\\n"
            f"[Nuevos Eventos a Condensar]:\\n{history_text}\\n\\n"
            "Redacta la Sinopsis Persistente actualizada:"
        )
        
      response = llm.invoke([HumanMessage(content=prompt)])
      return response.content
    except Exception as e:
        st.error(f"⚠️ Error generando memoria a largo plazo con Gemini: {e}")
        return current_summary

def manage_memory():
    if len(st.session_state.messages) > st.session_state.buffer_size:
        overflow = len(st.session_state.messages) - st.session_state.buffer_size
        oldest_msgs = st.session_state.messages[:overflow]
        
        with st.spinner("🌌 Transfiriendo corto plazo a la Memoria Omnisciente..."):
            new_summary = summarize_old_messages(oldest_msgs, st.session_state.summary)
            st.session_state.summary = new_summary
            
        st.session_state.messages = st.session_state.messages[overflow:]

# --- UI PRINCIPAL ---
def main():
    init_state()
    inject_custom_css()
    
    # --- MENÚ LATERAL ---
    with st.sidebar:
        st.title("🌌 OmniCharacterAI")
        st.markdown("*Impulsado por Gemini 1.5 Flash en la Nube*")
        st.markdown("---")
        
        selected_style = st.selectbox(
            "🎭 Personalidad Interactiva",
            ["Novela Visual", "Flash Fiction", "Épico/Hard-Roleplay"]
        )
        
        st.markdown("---")
        st.subheader("💾 Gestión de Partida")
        
        # Guardar en local JSON
        save_data = {
            "style": selected_style,
            "summary": st.session_state.summary,
            "messages": st.session_state.messages,
            "timestamp": datetime.now().isoformat()
        }
        json_data = json.dumps(save_data, indent=4, ensure_ascii=False)
        
        st.download_button(
            label="Descargar Partida (JSON)",
            data=json_data,
            file_name=f"omnicharacter_save_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
        # Cargar archivo JSON
        uploaded_file = st.file_uploader("Cargar Partida Guardada", type=["json"])
        if uploaded_file is not None:
            if st.button("Restaurar Historía"):
                data = json.load(uploaded_file)
                st.session_state.messages = data.get("messages", [])
                st.session_state.summary = data.get("summary", "")
                st.success("Trama restaurada perfectamente.")
                st.rerun()
        
        st.markdown("---")
        if st.button("Borrar Memoria (Nueva Partida)"):
            st.session_state.messages = []
            st.session_state.summary = ""
            st.rerun()
            
        st.markdown("---")
        with st.expander("👁️ Memoria Omnisciente (Tras Bambalinas)"):
            st.caption("Resumen persistente dinámico que evita el olvido del modelo a lo largo de chats inmensos.")
            st.info(st.session_state.summary if st.session_state.summary else "Aún no hay suficientes recuerdos.")

    # --- PANTALLA DE CHAT ---
    for msg in st.session_state.messages:
        avatar = "👤" if msg['role'] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
    # Formulario dinámico
    user_input = st.chat_input("Escribe tu próxima línea o acción...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            
        # Comprimir si superamos el buffer
        manage_memory()
        
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7, google_api_key=st.secrets["GOOGLE_API_KEY"])
            sys_prompt = get_system_prompt(selected_style, st.session_state.summary)
            
            lc_messages = [SystemMessage(content=sys_prompt)]
            for m in st.session_state.messages:
                if m["role"] == "user":
                    lc_messages.append(HumanMessage(content=m["content"]))
                else:
                    lc_messages.append(AIMessage(content=m["content"]))
                    
            with st.chat_message("assistant", avatar="🤖"):
                response_placeholder = st.empty()
                full_response = ""
                
                for chunk in llm.stream(lc_messages):
                    full_response += chunk.content
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Falla crítica contactando a Gemini. Verifica tu API Key o conexión a internet.\\nError: {e}")

if __name__ == "__main__":
    main()
