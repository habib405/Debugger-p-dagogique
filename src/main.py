import os
import json
import sqlite3
import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Nouveau SDK Google GenAI (pip install google-genai)
from google import genai

# ==========================================
# 1. CONFIGURATION ET CHARGEMENT DE LA CLÉ
# ==========================================
dossier_src = os.path.dirname(os.path.abspath(__file__))
dossier_racine = os.path.dirname(dossier_src)

# Recherche exhaustive des fichiers d'environnement
chemins_env = [
    os.path.join(dossier_src, ".env"),
    os.path.join(dossier_src, "code.env"),
    os.path.join(dossier_racine, ".env"),
    os.path.join(dossier_racine, "code.env")
]

for chemin in chemins_env:
    if os.path.exists(chemin):
        load_dotenv(dotenv_path=chemin, override=True)
        break

API_KEY = os.getenv("GEMINI_API_KEY")

MODELE_CHOISI = "models/gemini-1.5-flash" # Fallback par défaut
client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("\n--- SYNCHRONISATION GOOGLE AI ---")
        
        # Liste des modèles pour trouver le meilleur 'flash' disponible
        modeles_dispo = [m.name for m in client.models.list()]
        
        # Ordre de préférence
        preferences = ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]
        for pref in preferences:
            if pref in modeles_dispo:
                MODELE_CHOISI = pref
                break
        print(f"✅ Modèle actif : {MODELE_CHOISI}")
    except Exception as e:
        print(f"⚠️ Erreur initialisation SDK : {e}")
else:
    print("❌ ERREUR : GEMINI_API_KEY introuvable.")

# ==========================================
# 2. BASE DE DONNÉES SQLITE
# ==========================================
DB_PATH = os.path.join(dossier_src, "database.db")
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            langage TEXT,
            code TEXT,
            erreur TEXT,
            reponse_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. MODÈLES DE DONNÉES (Pydantic)
# ==========================================
class DebugRequest(BaseModel):
    langage: str = "Python"
    code: str
    erreur: str
    historique: str = ""

class Hypothese(BaseModel):
    titre: str
    explication: str
    test_suggere: str

class DebugResponse(BaseModel):
    explication_erreur: str
    hypotheses: list[Hypothese]
    encouragement: str

# ==========================================
# 4. INITIALISATION FASTAPI
# ==========================================
app = FastAPI(title="Debugger Pédagogique M1 DFS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 5. ROUTES API
# ==========================================
@app.post("/api/analyze", response_model=DebugResponse)
async def analyze_bug(request: DebugRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Client AI non initialisé.")

    try:
        prompt_content = f"""
        LANGAGE: {request.langage}
        CODE DE L'ÉTUDIANT:
        {request.code}
        
        ERREUR CONSOLE:
        {request.erreur}
        
        HISTORIQUE PRÉCÉDENT:
        {request.historique if request.historique else "Début de session."}
        """

        # Appel au SDK
        response = client.models.generate_content(
            model=MODELE_CHOISI,
            contents=prompt_content,
            config={
                "system_instruction": "Tu es un mentor pédagogue. NE DONNE JAMAIS LA SOLUTION. Explique le concept technique, propose des hypothèses et des tests en JSON.",
                "response_mime_type": "application/json",
                "response_schema": DebugResponse,
                "temperature": 0.2
            }
        )

        # Nettoyage et parsing du JSON
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        
        parsed_data = json.loads(raw_text)

        # Sauvegarde en base de données
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (timestamp, langage, code, erreur, reponse_json) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), request.langage, request.code, request.erreur, raw_text)
        )
        conn.commit()
        conn.close()

        return parsed_data

    except Exception as e:
        print(f"❌ ERREUR : {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "online", "model": MODELE_CHOISI, "db": "OK"}

@app.get("/api/history")
def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return {"history": rows}