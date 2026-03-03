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
