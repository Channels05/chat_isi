import os
import json
import re
from datetime import datetime
import streamlit as st
from babel.dates import format_date

# Configuración de la página y estilos
st.set_page_config(page_title="Chat de Instagram", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        .sender { color: #0084FF; font-weight: bold; }
        .message-left, .message-right {
            padding: 8px;
            margin: 3px 0;
            font-size: 0.9rem;
            border-radius: 10px;
        }
        .message-left { background-color: #E5E5EA; color: #333333; text-align: left; }
        .message-right { background-color: #D0E8FF; color: #0B3954; text-align: right; }
        .gallery-thumbnail { width: 100%; height: auto; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2); }
        .date-label { text-align: center; font-weight: bold; color: #555; padding: 5px 0; background-color: #f0f0f0; border-radius: 8px; margin: 10px 0; }

        body.dark-mode { background-color: #121212; color: #fff; }
        .message-left.dark-mode { background-color: #333; color: #ddd; }
        .message-right.dark-mode { background-color: #444; color: #fff; }
    </style>
""", unsafe_allow_html=True)

# Configuración de rutas
json_dir = 'C:\\Users\\Felipe\\Downloads\\easydoora_1294078478650384\\'
audio_dir = os.path.join(json_dir, 'audio')
video_dir = os.path.join(json_dir, 'videos')
photo_dir = os.path.join(json_dir, 'photos')

# Modo Oscuro
dark_mode = st.sidebar.checkbox("🌙 Modo Oscuro")
if dark_mode:
    st.markdown('<body class="dark-mode"></body>', unsafe_allow_html=True)

# Cargar archivos JSON
def load_json_files(json_dir):
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    messages = []
    for json_file in json_files:
        try:
            with open(os.path.join(json_dir, json_file), 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'messages' in data:
                    messages.extend(data['messages'])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            st.error(f"Error al procesar {json_file}: {e}")
    return messages

# Procesar mensajes
messages = load_json_files(json_dir)
for message in messages:
    if 'content' in message:
        try:
            message['content'] = message['content'].encode('latin1').decode('utf-8')
        except UnicodeDecodeError as e:
            st.warning(f"Error al decodificar mensaje: {e}")

# Ordenar mensajes por tiempo
sorted_messages = sorted(messages, key=lambda x: x['timestamp_ms'])
for message in sorted_messages:
    message['datetime'] = datetime.fromtimestamp(message['timestamp_ms'] / 1000)

# Filtros de fecha
if sorted_messages:
    min_date = min(msg['datetime'] for msg in sorted_messages).date()
    max_date = max(msg['datetime'] for msg in sorted_messages).date()
    start_date = st.sidebar.date_input("Fecha de inicio", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Fecha de fin", value=max_date, min_value=min_date, max_value=max_date)
else:
    st.error("No se encontraron mensajes.")
    st.stop()

# Filtrar mensajes
filtered_messages = [
    msg for msg in sorted_messages
    if start_date <= msg['datetime'].date() <= end_date
]

# Filtrar por palabra clave
keyword = st.sidebar.text_input("Buscar por palabra clave")
if keyword:
    keyword_regex = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
    filtered_messages = [
        msg for msg in filtered_messages if keyword_regex.search(msg.get('content', ''))
    ]

# Paginación
messages_per_page = 10
total_pages = (len(filtered_messages) + messages_per_page - 1) // messages_per_page
page = st.sidebar.number_input("Ir a la página:", min_value=1, max_value=max(1, total_pages), value=1)
start_idx = (page - 1) * messages_per_page
end_idx = start_idx + messages_per_page
page_messages = filtered_messages[start_idx:end_idx]

# Mostrar mensajes
def render_messages(messages):
    previous_date = None
    for message in messages:
        current_date = message['datetime'].date()
        if current_date != previous_date:
            formatted_date = format_date(message['datetime'], "EEEE, d 'de' MMMM 'de' y", locale='es')
            st.markdown(f"<div class='date-label'>{formatted_date}</div>", unsafe_allow_html=True)
            previous_date = current_date

        sender = message.get('sender_name', 'Unknown')
        content = message.get('content', '')
        sender = "Felipe" if sender in ["Felipe Canales H.", "Felipe Canales H.ð"] else sender

        message_html = f"<div class='message-right'>{content}</div>" if sender == "Felipe" else f"<div class='message-left'>{content}</div>"
        st.markdown(message_html, unsafe_allow_html=True)

render_messages(page_messages)

# Función para mostrar galerías
def render_gallery(media_gallery, media_dir, render_func, media_type="media"):
    for message in media_gallery:
        for media in message[media_type]:
            media_name = os.path.basename(media['uri'])
            media_path = os.path.join(media_dir, media_name)
            if os.path.exists(media_path):
                try:
                    render_func(media_path)
                except Exception as e:
                    st.warning(f"No se pudo cargar {media_name}: {e}")

# Mostrar galería de fotos
st.header("📸 Galería de Fotos")
photo_gallery = [msg for msg in sorted_messages if 'photos' in msg]
if photo_gallery:
    with st.expander("Ver todas las fotos"):
        render_gallery(photo_gallery, photo_dir, lambda x: st.image(x, caption="Foto", width=150), "photos")

# Mostrar galería de videos
st.header("🎥 Galería de Videos")
video_gallery = [msg for msg in sorted_messages if 'videos' in msg]
if video_gallery:
    with st.expander("Ver todos los videos"):
        render_gallery(video_gallery, video_dir, st.video, "videos")
