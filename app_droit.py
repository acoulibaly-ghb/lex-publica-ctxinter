import streamlit as st
import google.generativeai as genai
import os
import glob
from gtts import gTTS
import tempfile
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Lex Publica IA", 
    page_icon="⚖️",
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- 2. LE CSS (DESIGN & CORRECTIONS) ---
st.markdown("""
<style>
    /* 1. LAYOUT GLOBAL */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }
    
    /* 2. FORCE THÈME CLAIR */
    .stApp {
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
        color: #111827;
    }
    
    /* Cacher menu et footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 3. STYLE DES BULLES DE CHAT */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    /* Couleurs de fond des bulles */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F0F7FF;
        border: 1px solid #D0E3FF;
    }
    
    /* FORCE TEXTE NOIR DANS LES BULLES */
    .stChatMessage p, .stChatMessage li, .stChatMessage div {
        color: #111827 !important;
    }

    /* 4. SIDEBAR (BARRE LATÉRALE) */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }

    /* 5. BOUTONS */
    .stButton>button {
        background-color: #4F46E5;
        border: none;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #4338CA;
    }
    /* On force le texte du bouton en BLANC */
    .stButton>button p {
        color: #ffffff !important;
    }

    /* --- CORRECTIF FINAL SIDEBAR (TEXTE INVISIBLE) --- */
    
    /* Force TOUS les textes standards de la sidebar en noir */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div[data-testid="stMarkdown"] {
        color: #111827 !important;
    }
    
    /* --- LA LIGNE AJOUTÉE POUR "OPTIONS" --- */
    /* Force les TITRES (h1, h2, h3) de la sidebar en noir */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #111827 !important;
    }

    /* Cas spécifique pour l'Expander "Aide / Méthode" */
    .streamlit-expanderHeader p, 
    .streamlit-expanderHeader svg {
        color: #111827 !important;
        fill: #111827 !important;
    }
    
    /* Cas spécifique pour le switch "Réponses vocales" */
    [data-testid="stCheckbox"] label p {
        color: #111827 !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. LE TITRE (Désormais tout en haut) ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚖️</div>
        <h1 style="font-weight: 800; font-size: 2.2rem; margin-top: 0; color: #111827;">
            Lex Publica IA <span style="color: #4F46E5;">by Coulibaly</span>
        </h1>
        <p style="color: #6B7280; font-size: 1rem;">
            Votre assistant expert en droit du contentieux international.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- CLÉ API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante.")
    st.stop()

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
CONTEXTE : Tu es l'assistant pédagogique expert du Professeur Coulibaly.
BASE DE CONNAISSANCES : Strictement limitée aux fichiers PDF fournis.
RÈGLES :
1. Si question TEXTE : Réponds avec le cours.
2. Si question AUDIO : Commence par "Vous avez demandé : [Transcription]...".
3. Si QUIZ : Pose une question ouverte, attends la réponse.
"""

# --- FONCTIONS ---
@st.cache_resource
def load_and_process_pdfs():
    pdf_files = glob.glob("*.pdf")
    if not pdf_files: return None
    uploaded_refs = []
    try:
        for pdf in pdf_files:
            uploaded_refs.append(genai.upload_file(pdf, mime_type="application/pdf"))
        return uploaded_refs
    except: return None

if "chat_session" not in st.session_state:
    docs = load_and_process_pdfs()
    if docs:
        model = genai.GenerativeModel("gemini-2.5-flash-lite", system_instruction=SYSTEM_PROMPT)
        st.session_state.chat_session = model.start_chat(history=[{"role":"user", "parts":docs}, {"role":"model", "parts":["Prêt."]}])
        st.session_state.messages = []

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Options")
    audio_active = st.toggle("🔊 Réponses vocales", value=False)
    
    st.divider()
    
    # --- MODIFICATION : L'AUDIO EST DÉPLACÉ ICI ---
    # Cela libère l'écran principal comme demandé
    st.markdown("**🎙️ Mode Vocal**")
    audio_input = st.audio_input("Posez votre question ici")
    
    st.divider()
    
    if st.button("🃏 Pose-moi une colle !", use_container_width=True):
        if "chat_session" in st.session_state:
            with st.spinner("Recherche..."):
                response = st.session_state.chat_session.send_message("Pose-moi une question de vérification.")
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()

    with st.expander("🌐 Aide / Méthode"):
        st.markdown("**Méthodologie du Cas Pratique**")
        st.info("Rappel : Majeure, Mineure, Conclusion.")

# --- CHAT ---
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["content"] == "🎤 *[Question Vocale envoyée]*":
                st.markdown("🎤 *Question Vocale envoyée*")
            else:
                st.markdown(message["content"])

# --- SAISIE TEXTE (Reste en bas, standard des apps de chat) ---
text_input = st.chat_input("Posez votre question juridique...")

# --- LOGIQUE DE GESTION DES ENTRÉES ---
user_input = audio_input if audio_input else text_input
is_audio = audio_input is not None

if user_input:
    # Affiche message utilisateur
    msg_content = "🎤 *[Question Vocale envoyée]*" if is_audio else user_input
    st.session_state.messages.append({"role": "user", "content": msg_content})
    with st.chat_message("user"): st.markdown(msg_content)

    # Réponse IA
    if "chat_session" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Analyse..."):
                try:
                    if is_audio:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                            f.write(user_input.getvalue())
                            path = f.name
                        upl_file = genai.upload_file(path, mime_type="audio/wav")
                        response = st.session_state.chat_session.send_message(["Réponds selon tes règles de transcription.", upl_file])
                    else:
                        response = st.session_state.chat_session.send_message(user_input)
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})

                    if audio_active or is_audio:
                        clean = re.sub(r'[\*#]', '', response.text)
                        clean = re.sub(r'p\.\s*(\d+)', r'page \1', clean)
                        clean = clean.replace("Pr.", "Professeur")
                        tts = gTTS(text=clean, lang='fr')
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                            tts.save(fp.name)
                            with open(fp.name, "rb") as f:
                                st.audio(f, format="audio/mpeg")
                except Exception as e: st.error(f"Erreur: {e}")
