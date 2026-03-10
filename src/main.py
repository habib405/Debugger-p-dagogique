import os
import json
import sqlite3
import traceback
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# SDK Mistral AI
from mistralai import Mistral

# ==========================================
# 1. CONFIGURATION ET CHARGEMENT DE LA CLÉ
# ==========================================
dossier_src = os.path.dirname(os.path.abspath(__file__))
dossier_racine = os.path.dirname(dossier_src)

chemins_env = [
    os.path.join(dossier_src, ".env"),
    os.path.join(dossier_racine, ".env"),
    os.path.join(dossier_src, "code.env")
]

for chemin in chemins_env:
    if os.path.exists(chemin):
        load_dotenv(dotenv_path=chemin, override=True)
        break

API_KEY = os.getenv("MISTRAL_API_KEY")

MODELE_1 = "open-mistral-nemo"      
MODELE_2 = "mistral-small-latest"   
client = None

if API_KEY:
    try:
        client = Mistral(api_key=API_KEY)
        print("\n--- SYNCHRONISATION MISTRAL AI ---")
        print(f"✅ Client configuré avec succès.")
        print(f"🎯 Modèle principal : {MODELE_1}")
    except Exception as e:
        print(f"⚠️ Erreur initialisation Mistral : {e}")
else:
    print("❌ ERREUR : MISTRAL_API_KEY manquante.")

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
            prompt TEXT,
            reponse_json TEXT
        )
    ''')
    cursor.execute("PRAGMA table_info(history)")
    colonnes = [info[1] for info in cursor.fetchall()]
    if 'prompt' not in colonnes:
        cursor.execute("ALTER TABLE history ADD COLUMN prompt TEXT")
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. MODÈLES DE DONNÉES (Zéro contrainte de taille)
# ==========================================
class DebugRequest(BaseModel):
    langage: str = "Python"
    prompt: str = ""
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
app = FastAPI(title="Mentor Debugger Sympa")

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

@app.get("/")
def home():
    return {"status": "online", "provider": "Mistral AI", "mode": "friendly"}

@app.post("/api/analyze", response_model=DebugResponse)
async def analyze_bug(request: DebugRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Client Mistral non configuré.")

    prompt_final = request.prompt.strip()
    if not prompt_final:
        prompt_final = "Le champ était vide."

    # PROMPT SYSTÈME CORRIGÉ : On verrouille totalement la fuite de solutions
    instruction_systeme = """
    Tu es un mentor pédagogue expert en programmation, extrêmement chaleureux, poli et bienveillant.
    
    RÈGLES DE COMPORTEMENT (TRES IMPORTANT) :
    1. COURTOISIE : Si l'étudiant dit juste "bonjour", "salut" ou te remercie, sois très enthousiaste ! Réponds-lui poliment dans "explication_erreur", laisse "hypotheses" vide [], et mets un mot sympa dans "encouragement".
    2. AIDE AU CODE EFFICACE MAIS STRICTEMENT SOCRATIQUE : Tu DOIS ABSOLUMENT analyser et EXPLIQUER l'erreur, mais IL EST STRICTEMENT INTERDIT de donner la solution ou la ligne de code corrigée.
       - Explique le CONCEPT théorique (ex: "Python ne peut pas additionner du texte et des nombres").
       - Pointe la ligne qui pose problème.
       - RÈGLE D'OR : Ne dis JAMAIS "Modifie la ligne comme ceci : ...". Tu seras pénalisé si tu écris la réponse exacte.
       - Dans "test_suggere", propose UNIQUEMENT des actions d'investigation (ex: "Ajoute un print(type(ta_variable)) juste avant la ligne d'erreur pour vérifier son type") ou donne un rappel de cours générique avec d'autres noms de variables (ex: "Rappel : la fonction str(42) convertit un nombre en texte").
    
    FORMAT OBLIGATOIRE : Ta réponse DOIT être un JSON valide respectant EXACTEMENT ce schéma :
    {
      "explication_erreur": "Explication claire du concept sans donner la solution",
      "hypotheses": [
        {
          "titre": "Piste de réflexion",
          "explication": "Explication de la logique à corriger",
          "test_suggere": "Un test à faire (ex: un print) ou un exemple de cours générique. AUCUN CODE CORRIGÉ APPARTENANT À L'ÉTUDIANT ICI."
        }
      ],
      "encouragement": "Un petit mot sympa !"
    }
    """

    contenu_utilisateur = (
        f"LANGAGE INDIQUÉ: {request.langage}\n"
        f"MESSAGE DE L'ÉTUDIANT:\n{prompt_final}\n"
        f"CONTEXTE PRÉCÉDENT: {request.historique if request.historique else 'Aucun'}"
    )

    max_essais = 5
    response_content = None

    for essai in range(1, max_essais + 1):
        nom_modele = MODELE_1 if essai == 1 else MODELE_2
        
        try:
            print(f"📡 Analyse {essai}/{max_essais} sur {nom_modele}...")
            response = client.chat.complete(
                model=nom_modele,
                messages=[
                    {"role": "system", "content": instruction_systeme},
                    {"role": "user", "content": contenu_utilisateur}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            response_content = response.choices[0].message.content
            print(f"✅ Analyse réussie sur {nom_modele}")
            break 
            
        except Exception as e:
            err_msg = str(e).lower()
            if "404" in err_msg or "not found" in err_msg:
                continue
            elif "429" in err_msg or "too many requests" in err_msg:
                if essai < max_essais:
                    attente = 5 * essai
                    print(f"⏳ Quota épuisé pour {nom_modele}. Pause de {attente} secondes...")
                    await asyncio.sleep(attente)
                    continue 
                else:
                    raise HTTPException(status_code=429, detail="Le service est temporairement saturé.")
            else:
                raise HTTPException(status_code=500, detail=f"Une erreur inattendue est survenue avec l'IA: {str(e)}")

    if not response_content:
        raise HTTPException(status_code=429, detail="Impossible de joindre l'IA après 5 tentatives.")

    try:
        raw_text = response_content.strip()
        # Nettoyage des balises Markdown (ex: ```json ... ```)
        if "{" in raw_text and "}" in raw_text:
            debut = raw_text.find("{")
            fin = raw_text.rfind("}") + 1
            raw_text = raw_text[debut:fin]
            
        data = json.loads(raw_text)

        if not isinstance(data.get("hypotheses", []), list):
            data["hypotheses"] = []
        if "explication_erreur" not in data:
            data["explication_erreur"] = "Bonjour ! Comment puis-je t'aider aujourd'hui ?"
        if "encouragement" not in data:
            data["encouragement"] = "Je suis là pour toi !"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (timestamp, langage, prompt, reponse_json) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), request.langage, prompt_final, raw_text)
        )
        conn.commit()
        conn.close()

        return data

    except Exception as e:
        # Fallback ultra sécurisé en cas de problème de JSON (Rendu plus explicite)
        print(f"❌ Erreur critique IA : {str(e)}\nContenu reçu: {response_content}")
        return {
            "explication_erreur": f"⚠️ Oups, mon cerveau IA a eu un petit hoquet de formatage.",
            "hypotheses": [
                {
                    "titre": "Problème de communication",
                    "explication": "J'ai bien analysé ton code, mais ma réponse a été mal formatée et le serveur n'a pas pu la lire.",
                    "test_suggere": "Essaie de cliquer à nouveau sur 'Analyser le bug' ou donne-moi un peu plus de contexte sur l'erreur."
                }
            ],
            "encouragement": "Ne te décourage pas, c'est un bug de mon côté, pas du tien !"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)