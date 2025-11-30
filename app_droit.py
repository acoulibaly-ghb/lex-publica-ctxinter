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
    layout="centered", # On centre pour imiter le style Vercel
    initial_sidebar_state="expanded"
)

# --- 2. LE "MAQUILLAGE" CSS (DESIGN) ---
st.markdown("""
<style>
    /* Force le thème clair (au cas où) et police pro */
    .stApp {
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Supprimer le menu Hamburger et le footer Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Style des bulles de chat */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    /* Bulle de l'Assistant (Fond gris très pâle) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
    }

    /* Bulle de l'Étudiant (Fond bleu très pâle) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F0F7FF;
        border: 1px solid #D0E3FF;
    }

    /* Personnalisation de la Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }
    
    /* Boutons "Primary" (comme 'Pose-moi une colle') en violet/bleu */
    .stButton>button {
        color: white;
        background-color: #4F46E5; /* Le bleu/violet de votre capture */
        border: none;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #4338CA;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LE TITRE PERSONNALISÉ (STYLE VERCEL) ---
# On utilise du HTML pur pour avoir exactement le même look que votre capture
st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 3rem;">⚖️</div>
        <h1 style="font-weight: 800; font-size: 2.5rem; margin-top: 0; color: #111827;">
            Lex Publica IA <span style="color: #4F46E5;">by Coulibaly</span>
        </h1>
        <p style="color: #6B7280; font-size: 1.1rem;">
            Votre assistant expert en droit du contentieux international.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- RÉCUPÉRATION CLÉ API ---
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
    # Pas de message de chargement visible (plus propre)
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
    
    # Bouton Quiz stylisé
    if st.button("🃏 Pose-moi une colle !", use_container_width=True):
        if "chat_session" in st.session_state:
            with st.spinner("Recherche..."):
                response = st.session_state.chat_session.send_message("Pose-moi une question de vérification.")
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
    
    st.divider()
    
    # --- VOTRE IDÉE D'IFRAME ---
    # Par exemple, intégrer Légifrance ou le site de la CIJ
    with st.expander("🌐 Liens Utiles / Méthode"):
        st.markdown("**Méthodologie du Cas Pratique**")
        st.info("Rappel : Majeure, Mineure, Conclusion.")
        # Exemple d'iframe (Site du Conseil d'État ou autre)
        # Note : Beaucoup de sites bloquent les iframes, mais on peut mettre un PDF d'aide.
        st.markdown("[Voir le site de la CIJ](https://www.icj-cij.org/fr)", unsafe_allow_html=True)

# --- CHAT ---
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["content"] == "🎤 *[Question Vocale envoyée]*":
                st.markdown("🎤 *Question Vocale envoyée*")
            else:
                st.markdown(message["content"])

# --- ENTRÉES ---
audio_input = st.audio_input("🎙️")
text_input = st.chat_input("Posez votre question juridique...")

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
