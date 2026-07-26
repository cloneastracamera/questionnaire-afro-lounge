# Questionnaire Afro Lounge — Python/Flask

## Installation dans VS Code

1. Ouvrez le dossier `questionnaire_afro_lounge` dans VS Code.
2. Ouvrez **Terminal > Nouveau terminal**.
3. Créez un environnement virtuel :

   Windows :

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

   macOS/Linux :

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Installez Flask :

   ```bash
   pip install -r requirements.txt
   ```

5. Lancez le sondage :

   ```bash
   python app.py
   ```

6. Ouvrez `http://127.0.0.1:5000` dans votre navigateur.

## Récupérer les réponses

Les réponses sont enregistrées automatiquement dans `reponses.db`.

Pour télécharger les réponses sous Excel/CSV, ouvrez :

`http://127.0.0.1:5000/export.csv`

## Mise en ligne

Cette version fonctionne localement. Pour permettre à d’autres personnes de
répondre, il faudra ensuite l’héberger, par exemple sur Render, Railway ou un
serveur compatible Python.
