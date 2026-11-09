# Log Analyzer

Ce projet Python analyse les logs SSH d'un serveur Linux (auth.log) pour voir qui essaie de se connecter, depuis quel pays et avec quels noms d'utilisateur.

Le programme lit les fichiers du dossier data (meme les .gz), garde avec des regex les mots de passe faux, les users invalides et les connexions reussies, puis cherche le pays de chaque IP avec ipinfo.io. Les resultats sont enregistres dans storage/events.csv et storage/locations.csv, et le dashboard matplotlib affiche les tentatives echouees par pays, les tentatives reussies par user et les tentatives avec un user invalide.

Pour l'installer il faut Python 3.14 et uv, puis "uv sync". Pour le lancer c'est "uv run main.py", ou "uv run main.py reload" si on change les fichiers de data. On utilise seulement matplotlib et requests. Sans token ipinfo bloque vite, donc on peut en mettre un avec $env:IPINFO_TOKEN = "ton_token". Les IPs deja trouvees restent dans locations.csv et ne sont pas redemandees.

Il n'y a pas de base de donnees parce que deux csv suffisent pour quelques milliers de lignes. Chaque module a son propre fichier de log dans le dossier logs pour savoir ou chercher en cas d'erreur.

Dans nos logs on trouve 16 361 mots de passe faux venant de 1 853 IPs, surtout sur root, et 3 166 tentatives avec un user qui n'existe pas. La seule connexion reussie vient du reseau local (adminesisa depuis 10.10.33.81), donc personne de l'exterieur n'est rentre.
