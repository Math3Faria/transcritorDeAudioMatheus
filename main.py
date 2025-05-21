import streamlit as st
from pydub import AudioSegment
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
import whisper
import time
import random

# --- Configuração Inicial ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Page Config (must be at the top) ---
st.set_page_config(
    page_title="Transcritor e Tradutor de Áudio",
    layout="centered"
)

# --- Custom CSS for Instagram-like look and GIF background ---
st.markdown(
    """
    <style>
    /* GIF Background */
    .stApp {
        background-image: url("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHFheHB0bmtmZHdsMXM2OGFuZnR2cTc4bmxxdmEwY3Bic3gyZjd5ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/h4HHnU9RXd1Dvc24Gs/giphy.gif"); /* Seu GIF URL */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed; /* Mantém o GIF estático ao rolar */
    }

    /* Main Container Styling - Mais transparente! */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 1.5rem; /* Aumentado o padding lateral */
        padding-left: 1.5rem;  /* Aumentado o padding lateral */
        padding-bottom: 2rem;
        background-color: rgba(255, 255, 255, 0.4); /* Menos opaco, mais transparente */
        border-radius: 20px; /* Bordas mais arredondadas */
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Sombra mais pronunciada */
        max-width: 750px; /* Um pouco mais largo para melhor leitura */
        margin: auto; /* Centraliza o container */
        backdrop-filter: blur(5px); /* Efeito de desfoque para o conteúdo */
    }

    /* Title Styling */
    h1 {
        color: #1a1a1a; /* Quase preto para forte contraste */
        text-align: center;
        margin-bottom: 1.8rem; /* Mais espaçamento abaixo do título */
        font-size: 2.8em; /* Título maior e mais impactante */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Fonte mais moderna */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1); /* Sombra sutil no texto */
    }

    /* Subheader Styling */
    h2, h3, h4, h5, h6 {
        color: #333333;
        margin-top: 2rem; /* Mais espaçamento acima dos sub-cabeçalhos */
        margin-bottom: 1.2rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Markdown text */
    p, .stMarkdown, label {
        color: #444444; /* Cor do texto um pouco mais escura para legibilidade */
        line-height: 1.7; /* Mais espaço entre as linhas */
        font-size: 1.05em; /* Texto um pouco maior */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(to right, #007bff, #00bcd4); /* Gradiente de azul para ciano */
        color: white;
        border-radius: 10px; /* Bordas mais arredondadas */
        padding: 0.8rem 1.8rem; /* Mais padding para o botão */
        font-size: 1.2em; /* Texto do botão maior */
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2); /* Sombra mais suave */
        transition: all 0.3s ease; /* Transição para hover */
        cursor: pointer;
    }

    .stButton > button:hover {
        transform: translateY(-2px); /* Efeito de "levantar" no hover */
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); /* Sombra mais intensa no hover */
        background: linear-gradient(to right, #0056b3, #008c9e); /* Gradiente mais escuro no hover */
    }

    /* File Uploader Styling */
    .stFileUploader label {
        color: #333333;
        font-weight: bold;
        font-size: 1.1em;
    }

    /* Selectbox Styling */
    .stSelectbox label {
        color: #333333;
        font-weight: bold;
        font-size: 1.1em;
    }

    /* Info, Warning, Error, Success Messages - Cores mais suaves */
    .stAlert {
        border-radius: 10px; /* Mais arredondado */
        padding: 1.2rem; /* Mais padding */
        margin-top: 1.2rem;
        margin-bottom: 1.2rem;
        font-size: 1.05em;
    }

    .stAlert.info {
        background-color: #e3f2fd; /* Azul mais claro */
        color: #2196f3; /* Azul primário */
        border-left: 6px solid #2196f3;
    }
    .stAlert.warning {
        background-color: #fff3e0; /* Laranja suave */
        color: #ff9800; /* Laranja primário */
        border-left: 6px solid #ff9800;
    }
    .stAlert.error {
        background-color: #ffebee; /* Vermelho claro */
        color: #f44336; /* Vermelho primário */
        border-left: 6px solid #f44336;
    }
    .stAlert.success {
        background-color: #e8f5e9; /* Verde claro */
        color: #4caf50; /* Verde primário */
        border-left: 6px solid #4caf50;
    }

    /* Horizontal Rule */
    hr {
        border-top: 1px solid #dddddd; /* Linha mais clara */
        margin-top: 2.5rem;
        margin-bottom: 2.5rem;
    }

    /* Footer Text */
    .stMarkdown small {
        color: #777777;
        text-align: center;
        display: block;
        margin-top: 2rem;
        font-size: 0.9em;
    }

    /* Adicional: Player de áudio mais discreto */
    audio {
        width: 100%;
        margin-top: 1rem;
        margin-bottom: 1rem;
        filter: invert(10%); /* Escurece um pouco o player para combinar */
    }

    </style>
    """,
    unsafe_allow_html=True
)

# --- API Key Check ---
if not GEMINI_API_KEY:
    st.error("❌ Erro: Chave da API Gemini não encontrada. Adicione GEMINI_API_KEY ao seu arquivo .env.")
    st.stop()
else:
    genai.configure(api_key=GEMINI_API_KEY)

st.title("Transcritor e Tradutor de Áudio do Matheus🤯")

st.markdown("""
    Faça upload de um áudio em MP3.
""")

# Mapeamento de idiomas para a API Gemini
LANGUAGE_MAPPING = {
    "Português": "Portuguese",
    "Inglês": "English",
    "Espanhol": "Spanish",
    "Francês": "French",
    "Alemão": "German",
    "Italiano": "Italian",
    "Japonês": "Japanese",
    "Chinês": "Chinese"
}

# --- Audio Upload Section ---
st.subheader("Upload de Áudio")
uploaded_file = st.file_uploader("Envie um arquivo de áudio (MP3)", type=["mp3"])

target_language_display = st.selectbox(
    "Idioma de destino para a tradução:",
    list(LANGUAGE_MAPPING.keys()),
    index=1  # Inglês como padrão
)
target_language_for_gemini = LANGUAGE_MAPPING[target_language_display]

# Função para implementar backoff exponencial
def exponential_backoff_retry(func, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if '429' in str(e):
                sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                st.warning(f"⚠️ Limite de taxa excedido. Tentando novamente em {sleep_time:.2f} segundos...")
                time.sleep(sleep_time)
            else:
                raise e
    raise Exception("Máximo de tentativas excedido.")

if uploaded_file:
    st.audio(uploaded_file, format='audio/mp3')

    if st.button("✨ Transcrever e Traduzir", type="primary"):
        st.info("🔄 Iniciando o processamento do áudio... Isso pode levar alguns segundos ou minutos, dependendo do tamanho do arquivo e do modelo Whisper.")

        temp_mp3_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                tmp_mp3.write(uploaded_file.read())
                temp_mp3_path = tmp_mp3.name

            # --- Transcrição usando OpenAI Whisper ---
            st.info("🎧 Carregando modelo Whisper e transcrevendo áudio...")
            model_whisper = whisper.load_model("base")
            result = model_whisper.transcribe(temp_mp3_path, language="pt")
            transcription = result["text"].strip()

            st.subheader("📝 Transcrição:")
            st.write(transcription if transcription else "Nada transcrito pelo Whisper.")

            # --- Tradução com Gemini API ---
            st.subheader(f"🌍 Tradução para {target_language_display}:")
            if transcription:
                try:
                    def translate():
                        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                        trans_prompt = f"Traduza o seguinte texto para {target_language_for_gemini}:\n\n{transcription}"
                        trans_response = gemini_model.generate_content(trans_prompt)
                        return trans_response.text.strip()

                    translation = exponential_backoff_retry(translate)
                    st.write(translation)

                except Exception as e:
                    st.error(f"❌ Erro na tradução com a API Gemini: {e}")
                    st.warning("Verifique sua chave da API Gemini, sua conexão com a internet e se você não excedeu os limites de uso.")
                    st.write(f"Detalhes do erro: {type(e).__name__}: {e.args}")
            else:
                st.info("Não há texto para traduzir, pois a transcrição falhou.")

        except Exception as e:
            st.error("❌ Ocorreu um erro durante o processamento (verifique instalação do Whisper/PyTorch ou arquivo de áudio).")
            st.exception(e)

        finally:
            if temp_mp3_path and os.path.exists(temp_mp3_path):
                os.remove(temp_mp3_path)
            st.success("✅ Processamento concluído!")

st.markdown("---")
st.markdown("<small>Desenvolvido por Matheus Faria | Powered by Streamlit & Google Gemini API</small>", unsafe_allow_html=True)