# Log Analyzer

Projet Python qui analyse les logs SSH d'un serveur Linux (les fichiers `auth.log`) pour voir qui essaie de se connecter, depuis ou, et avec quels noms d'utilisateur.

Quand on ouvre un `auth.log` a la main on voit des milliers de lignes `Failed password for root from ...`, c'est des bots qui testent des mots de passe en boucle. Le but du projet c'est de faire le tri dans tout ca et de sortir des stats + un dashboard.

## Ce que le programme fait

1. **ingestion** : il lit tous les fichiers `auth.log*` du dossier `data/`, meme ceux compresses (`auth.log.3.gz`, `auth.log.4.gz`)
2. **process** : avec des regex il garde seulement les lignes de `sshd` qui nous interessent :
   - `Failed password for ...` -> mot de passe faux
   - `Invalid user ...` -> le user n'existe meme pas sur le serveur
   - `Accepted password for ...` -> connexion reussie
   - `message repeated 4 times: [...]` -> compte pour 4 tentatives, pas 1

   Ensuite il cherche le pays de chaque IP avec l'API [ipinfo.io](https://ipinfo.io)
3. **storage** : les resultats sont enregistres dans des fichiers csv
4. **serving** : affiche le rapport dans le terminal et le dashboard avec matplotlib

## Dashboard

La premiere ligne du dashboard c'est les 3 graphes demandes :

- nombre de tentatives echouees par pays
- nombre de tentatives reussies par user
- tentatives echouees avec invalid user (les 15 noms les plus testes)

Et en dessous j'ai garde 3 graphes en plus qui aident a comprendre : le total failed / invalid / success, les tentatives par jour et les 15 IPs qui attaquent le plus.

## Structure du projet

```
log_analyser/
├── main.py                      # lance tout dans l'ordre + configure les logs
├── data/                        # les fichiers auth.log a analyser
├── ingestion/
│   └── raw.py                   # lecture des fichiers (.log et .gz)
├── process/
│   ├── extract_transforme.py    # regex + calcul des stats
│   └── geolocation.py           # IP -> pays avec ipinfo
├── storage/
│   └── storage.py               # lecture / ecriture des csv
├── serving/
│   └── graphs.py                # rapport + graphes
└── logs/                        # cree tout seul au lancement
```

## Installation

Il faut Python 3.14 et `uv`.

```bash
uv sync
```

On utilise seulement `matplotlib` et `requests`, tout le reste vient de Python (`re`, `os`, `gzip`, `csv`, `logging`).

## Lancement

```bash
uv run main.py
```

La premiere fois il lit les logs et cree `storage/events.csv`. Les fois d'apres il relit directement le csv, c'est plus rapide.
Si on change les fichiers dans `data/`, il faut relancer avec `reload` pour tout relire :

```bash
uv run main.py reload
```

### Token ipinfo

Sans token, ipinfo bloque assez vite (erreur 429) et une partie des IPs reste en `Unknown`. Avec un compte gratuit sur ipinfo.io on a un token, et il suffit de le mettre dans le terminal avant de lancer :

```powershell
$env:IPINFO_TOKEN = "ton_token"
uv run main.py
```

Les IPs deja trouvees sont gardees dans `storage/locations.csv`, donc on ne redemande jamais une IP deja connue. Celles qui n'ont pas marche sont reessayees au prochain lancement. Et on commence toujours par les IPs qui attaquent le plus, comme ca si on est bloque, les plus importantes sont deja localisees.

## Pourquoi pas de base de donnees

J'avais essaye avec MariaDB au debut mais c'etait trop lourd pour ce qu'on fait (il fallait installer et lancer un serveur juste pour quelques milliers de lignes). Maintenant tout est dans 2 csv dans `storage/` :

- `events.csv` : une ligne par tentative (date, status, user, ip, nombre)
- `locations.csv` : le pays et la ville de chaque IP

Ils ne sont pas sur le git parce qu'ils sont recrees par le programme.

## Logs de l'application

Chaque module a son propre fichier de log dans `logs/`, comme ca quand ca plante on sait direct ou chercher :

| fichier | erreurs enregistrees |
|---|---|
| `ingestion.log` | dossier `data/` introuvable, aucun fichier auth.log, fichier illisible (droits), `.gz` corrompu, fichier vide |
| `process.log` | mois inconnu dans une ligne, aucune ligne ssh trouvee, ipinfo : timeout, pas d'internet, limite atteinte (429), reponse pas en json, IPs sans pays |
| `storage.log` | csv introuvable ou corrompu, impossible d'ecrire le csv (par exemple s'il est ouvert dans Excel) |
| `serving.log` | graphe vide (pas de donnees) |
| `main.log` | debut / fin, rien a analyser, et toutes les erreurs imprevues avec la traceback complete |

Dans le terminal on voit seulement les warnings et les erreurs, le reste va dans les fichiers.

## Ce qu'on trouve dans nos logs

Sur les 4 fichiers de `data/` :

- **16 361** mots de passe faux, depuis **1 853** IPs differentes
- `root` est le user le plus teste de loin (13 090 tentatives)
- **3 166** tentatives avec un user qui n'existe pas (`admin`, `esisa`, `ubuntu`, `user`, `test`...)
- **1 seule** connexion reussie : `adminesisa` depuis `10.10.33.81`, une IP du reseau local donc c'est normal
- les IPs qui attaquent le plus sont des plages `45.148.10.x` (Pays-Bas) et `92.118.39.x` (Roumanie)

Conclusion : le serveur se fait attaquer non-stop mais personne de l'exterieur n'a reussi a rentrer. Ca vaudrait quand meme le coup d'interdire le login root en SSH et d'installer fail2ban.

## Difficultes

- les fichiers `.gz` qu'il faut decompresser avec `gzip` avant de les lire
- le syslog ne donne pas l'annee dans la date (`May 24 01:14:12`)
- la limite de requetes d'ipinfo, d'ou le cache csv
- les lignes "message repeated N times" qu'on comptait comme une seule tentative au debut
