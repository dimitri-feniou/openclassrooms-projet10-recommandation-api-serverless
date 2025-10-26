# Lancer l'Application Streamlit avec Azure Functions

## Vue d'Ensemble

L'application Streamlit `app_st.py` utilise maintenant l'API Azure Functions au lieu de charger les données localement. C'est une architecture serverless complète !

```
┌─────────────────────┐
│  Streamlit (UI)     │  ← Interface utilisateur web
└──────────┬──────────┘
           │ HTTP Requests
           ▼
┌─────────────────────┐
│ Azure Functions     │  ← API Serverless
│ - /api/health       │
│ - /api/users        │
│ - /api/recommend    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Azure Blob Storage  │  ← Données
└─────────────────────┘
```

## Option 1: Utiliser l'API Azure (Recommandé)

### Prérequis
1. Avoir déployé l'API Azure Functions (voir deploy.sh)
2. Installer les dépendances Streamlit

### Installation

```bash
# Installer les dépendances Streamlit
pip install -r requirements_streamlit.txt
```

### Lancement

```bash
# Définir l'URL de votre API Azure Functions
export API_URL="https://func-recommender-api.azurewebsites.net"

# Lancer Streamlit
streamlit run app_st.py
```

L'application sera disponible sur **http://localhost:8501**

### Changer l'URL de l'API

Vous pouvez changer l'URL de l'API de 3 façons :

**1. Via variable d'environnement :**
```bash
export API_URL="https://votre-function-app.azurewebsites.net"
streamlit run app_st.py
```

**2. Via l'interface Streamlit :**
- Dans la sidebar, section "Configuration API"
- Entrez la nouvelle URL
- Cliquez sur "Mettre à jour l'API"

**3. Pour tester en local avec l'API locale :**
```bash
# Terminal 1: Lancer Azure Functions localement
func start

# Terminal 2: Lancer Streamlit avec l'API locale
export API_URL="http://localhost:7071"
streamlit run app_st.py
```

## Option 2: Mode Autonome (Sans API)

Si vous voulez utiliser Streamlit sans l'API Azure Functions :

```bash
# Utilisez l'ancienne version qui charge les données localement
cd ../api
streamlit run app_st.py
```

## Fonctionnalités

### Interface Streamlit
- ✅ Connexion automatique à l'API Azure
- ✅ Affichage du statut de l'API (connectée/déconnectée)
- ✅ Métriques en temps réel (utilisateurs, articles, interactions)
- ✅ Sélection d'utilisateur par ID ou aléatoire
- ✅ Paramétrage du nombre de recommandations (1-20)
- ✅ Affichage des résultats avec scores et métadonnées
- ✅ Statistiques utilisateur
- ✅ Liste complète des utilisateurs
- ✅ Configuration de l'URL API dans l'interface

### Endpoints Utilisés

L'application appelle 3 endpoints de l'API :

1. **GET /api/health**
   - Vérifie l'état de l'API
   - Récupère les statistiques globales

2. **GET /api/users**
   - Liste tous les utilisateurs
   - Utilisé pour le bouton "Utilisateur aléatoire"

3. **GET /api/recommend?user_id=X&n=5&with_meta=true**
   - Génère les recommandations
   - Inclut les métadonnées des articles

## Configuration

### Variables d'Environnement

```bash
# URL de l'API Azure Functions
export API_URL="https://func-recommender-api.azurewebsites.net"

# Ou pour test local
export API_URL="http://localhost:7071"
```

### Fichier .streamlit/config.toml (Optionnel)

Créez `.streamlit/config.toml` pour personnaliser :

```toml
[theme]
primaryColor = "#0078D4"  # Azure blue
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"

[server]
port = 8501
enableCORS = false
```

## Avantages de cette Architecture

### ✅ Serverless Complet
- Streamlit : Interface utilisateur
- Azure Functions : API backend
- Azure Blob Storage : Données

### ✅ Séparation des Préoccupations
- Frontend (Streamlit) et Backend (Azure Functions) indépendants
- Peut déployer chaque partie séparément
- L'API peut être utilisée par d'autres clients

### ✅ Scalabilité
- Streamlit peut être déployé sur Azure Container Apps
- Azure Functions scale automatiquement
- Pas de gestion d'infrastructure

### ✅ Développement Local Facile
- Tester l'API localement avec `func start`
- Tester Streamlit localement
- Changer l'URL de l'API facilement



