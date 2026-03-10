Réalisations (Séance actuelle)

Nous avons finalisé l'architecture de base et la connectivité de l'outil :

Backend FastAPI : Serveur robuste capable de traiter les requêtes d'analyse en temps réel.

Intégration Google AI (nouveau SDK) : Migration réussie vers google-genai pour utiliser Gemini 2.0 Flash.

Interface Polyglotte : Frontend capable de gérer différents langages (Python, JS, PHP, Java).

Persistance SQLite : Mise en place d'une base de données locale pour sauvegarder l'historique des sessions.

Système de Résilience : Implémentation d'un algorithme de backoff exponentiel pour gérer les limites de quota (erreurs 429).

 Difficultés et Erreurs Résolues

Le développement a été marqué par plusieurs défis techniques majeurs :

Gestion des versions d'API : Résolution d'erreurs 404 liées aux noms changeants des modèles Gemini (migration de models/gemini-1.5-flash vers les dernières versions).

Configuration de l'environnement : Correction des problèmes de détection du fichier .env selon le répertoire d'exécution (src vs racine).

Quotas de l'offre gratuite : Adaptation du code pour contrer l'erreur RESOURCE_EXHAUSTED (429) via des tentatives automatiques retardées.

Parsing JSON : Nettoyage des réponses de l'IA pour extraire uniquement le contenu structuré, même en présence de balises Markdown parasites.

Prochaine Séance

Pour la suite du projet, nous nous concentrerons sur :

Amélioration de l'UI : Ajout de la coloration syntaxique (Prism.js ou Highlight.js) pour rendre le code plus lisible.

Dashboard d'Historique : Création d'une page dédiée pour consulter et filtrer les anciennes analyses stockées en base SQLite.

Affinement du Prompt : Optimisation des instructions "système" pour rendre le mentor encore plus stimulant et éviter toute tentative de "triche" de l'utilisateur.


09/03/2026 


j'avais pusher par erreur la cle API sur GIT aujouhuit j'ai commencer par faire un git Ignore sur le fichier .env qui contient la cle API 

09/03/2026 
Bilan : Défis et Résolutions

Nous avons transformé notre script en un serveur backend robuste et pédagogique. Voici les bugs corrigés :

1. Limites d'API (Erreurs 429 & 404)

Problème : Quotas gratuits vite épuisés (429) et blocages sur des modèles introuvables (404).

Solution : Ajout d'un délai progressif entre les essais (5s, 10s...) et passage immédiat au modèle de secours en cas d'erreur 404.

2. Erreur "422 Unprocessable Content"

Problème (Côté IA) : Mistral inventait sa propre structure JSON, ce qui faisait violemment planter Pydantic (le validateur de FastAPI) qui attendait des champs très précis (explication_erreur, hypotheses).

Le problème (Côté Utilisateur) : Si tu tapais un prompt trop court (ex: "a" ou "printf"), FastAPI rejetait la requête avant même de l'envoyer à l'IA à cause de la règle min_length=10.

La solution : * Nous avons "moulé" l'IA en incluant le squelette JSON exact dans le prompt système.

Nous avons créé un Patch Anti-422 en supprimant les limites de taille et en rendant l'API ultra-flexible pour accepter tous les formats (anciens comme nouveaux).

3. Les bugs d'interface (Frontend)

Le problème [object Object] : Quand FastAPI renvoyait une erreur de validation détaillée (sous forme de liste JSON), JavaScript ne savait pas l'afficher et mettait [object Object].

L'attente infinie : Parfois l'IA mettait 45 secondes à répondre, donnant l'impression que le site était planté.

La solution : Nous avons forcé le JSON.stringify pour lire les vraies erreurs, ajouté un bouton "Analyse en cours...", et mis en place un "Timeout" (coupure automatique après 60 secondes avec un message d'erreur clair).

4. Le "Biais de Serviabilité" de l'IA (Le plus gros défi pédagogique)

Le problème : Malgré la consigne "Ne donne pas la solution", l'IA était tellement programmée pour rendre service qu'elle corrigeait systématiquement ton code (ex: te dire de remplacer 1 par str(1)).

La solution (Prompt Socratique Extrême) : * Nous avons interdit des mots-clés comme "remplace", "modifie".

Nous avons forcé l'IA à répondre par des questions ou des exemples génériques (totalement déconnectés de ton code).

Nous avons baissé la température à 0.1 pour supprimer son "improvisation" et la forcer à obéir strictement aux règles de formatage.