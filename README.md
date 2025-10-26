# Lancer l'Application Streamlit avec Azure Functions


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


## Endpoints Utilisés

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





