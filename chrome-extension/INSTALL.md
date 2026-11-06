# Installation de l'extension « YouTube Sentiment Analyzer »

Cette extension Chrome analyse le sentiment (négatif, neutre, positif) des commentaires d'une vidéo YouTube. Elle envoie les commentaires à une API déployée dans le cloud (GitHub Codespaces) et affiche les résultats dans un popup.

## 1. Prérequis

- Google Chrome (ou un navigateur basé sur Chromium).
- Une connexion internet.
- L'API doit être en ligne : voir la section 5 (l'API cloud ne répond que lorsque le Codespace est actif).

## 2. Installation

1. **Décompressez** l'archive `youtube-sentiment-extension.zip` dans un dossier de votre choix (par exemple `Documents\youtube-sentiment-extension`). Ne supprimez pas ce dossier après l'installation : Chrome l'utilise.
2. Ouvrez Chrome et tapez `chrome://extensions` dans la barre d'adresse.
3. Activez le **Mode développeur** (interrupteur en haut à droite).
4. Cliquez sur **Charger l'extension non empaquetée**.
5. Sélectionnez le dossier décompressé, celui qui contient directement le fichier `manifest.json`.
6. La carte « YouTube Sentiment Analyzer » apparaît dans la liste, sans bouton rouge « Erreurs ».
7. Cliquez sur l'icône « puzzle » de la barre Chrome, puis sur l'épingle à côté de l'extension pour l'afficher en permanence.

## 3. Utilisation rapide

1. Ouvrez une vidéo YouTube (adresse de la forme `youtube.com/watch?v=...`) qui a des commentaires.
2. Cliquez sur l'icône de l'extension.
3. Choisissez le nombre de commentaires à analyser et le serveur **Cloud**.
4. Cliquez sur **Analyser cette vidéo**.
5. Laissez le popup ouvert pendant l'analyse : s'il se ferme, l'analyse est interrompue.

Les résultats (statistiques, liste des commentaires, filtres) s'affichent ensuite. Pour le détail des fonctionnalités, consultez le guide utilisateur.

## 4. Mise à jour ou modification

Après toute modification d'un fichier de l'extension (par exemple `config.js`) :

1. Retournez sur `chrome://extensions`.
2. Cliquez sur la flèche circulaire de la carte de l'extension.
3. Rechargez l'onglet YouTube.

## 5. Serveurs : Cloud ou Local

L'extension peut utiliser deux serveurs, au choix dans le popup.

### Cloud (par défaut)

L'API tourne dans un Codespace GitHub. Son adresse est définie dans `config.js` :

```js
cloud: "https://expert-rotary-phone-pjx5jxgp76rp29wqx-7860.app.github.dev",
```

Important : un Codespace s'arrête après environ 30 minutes d'inactivité. Si le popup affiche « Serveur injoignable » ou si l'adresse répond par une erreur 502, le Codespace doit être redémarré. Pour vérifier que l'API est active, ouvrez `https://expert-rotary-phone-pjx5jxgp76rp29wqx-7860.app.github.dev` dans le navigateur : la réponse doit contenir `"model_loaded": true`.

Pour utiliser une autre adresse d'API :

1. Ouvrez `config.js` avec un éditeur de texte.
2. Remplacez l'adresse de `cloud` (sans `/` à la fin).
3. Vérifiez que `manifest.json` autorise ce domaine dans `host_permissions` (`https://*.app.github.dev/*` pour Codespaces).
4. Rechargez l'extension (section 4).

### Local

Cette option utilise l'API installée sur votre ordinateur. Elle nécessite Python 3.10 ou supérieur et le dépôt GitHub du projet.

```bash
git clone <lien-du-depot-github>
cd <nom-du-depot>
pip install -r requirements.txt
python -m uvicorn app_api:app --port 8000
```

Vérifiez ensuite `http://localhost:8000/health`, puis choisissez **Local** dans le menu « Serveur » du popup.

## 6. Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| « Serveur injoignable » | API arrêtée, Codespace éteint ou port privé | Relancer le Codespace et le conteneur, vérifier que le port 7860 est **Public**, ou passer en mode **Local** |
| Erreur API (404) | Mauvaise adresse dans `config.js`, ou extension non rechargée | Corriger l'adresse (sans `/` final), recharger l'extension |
| « Ouvrez une vidéo YouTube » | Le popup est ouvert sur une autre page | Aller sur une page de vidéo `youtube.com/watch?v=...` |
| « Aucun commentaire trouvé » | Commentaires désactivés ou non chargés | Faire défiler la page pour afficher les commentaires, puis relancer l'analyse |
| Requête bloquée par Chrome | Domaine absent de `host_permissions` | Ajouter le domaine dans `manifest.json` et recharger l'extension |
| L'extension ne se charge pas | Mauvais dossier sélectionné | Sélectionner le dossier qui contient directement `manifest.json` |

## 7. Contenu de l'archive

```
youtube-sentiment-extension/
├── manifest.json    Configuration et permissions de l'extension
├── content.js       Extraction des commentaires sur la page YouTube
├── popup.html       Structure du popup
├── popup.css        Style du popup (thèmes clair et sombre)
├── popup.js         Appels à l'API, statistiques, filtres, copie, export
├── config.js        Adresses des serveurs et paramètres
├── icons/           Icônes de l'extension
└── INSTALL.md       Ce fichier
```
