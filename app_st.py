# app_st.py - Streamlit application using Azure Functions API
import os
import requests
import pandas as pd
import numpy as np
import streamlit as st

# API Configuration - can be changed via environment variable or UI
DEFAULT_API_URL = os.environ.get("API_URL", "https://func-recommender-api.azurewebsites.net")

# Initialize session state
if 'api_url' not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if 'random_user_id' not in st.session_state:
    st.session_state.random_user_id = None
if 'user_ids' not in st.session_state:
    st.session_state.user_ids = []

# Page configuration
st.set_page_config(page_title="Système de Recommandation d'Articles", layout="wide")

# API Call Functions
@st.cache_data(ttl=300, show_spinner=False)
def get_health_status(api_url):
    """Get API health status"""
    try:
        response = requests.get(f"{api_url}/api/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@st.cache_data(ttl=60, show_spinner=False)
def get_users_list(api_url):
    """Get list of users from API"""
    try:
        response = requests.get(f"{api_url}/api/users", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des utilisateurs : {e}")
        return []

def get_recommendations(api_url, user_id, n=5):
    """Get recommendations for a user"""
    try:
        params = {'user_id': user_id, 'n': n, 'with_meta': 'true'}
        response = requests.get(f"{api_url}/api/recommend", params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error(f"L'utilisateur {user_id} n'existe pas dans la base de données.")
        elif e.response.status_code == 400:
            st.error(f"Paramètres invalides")
        else:
            st.error(f"Erreur API : {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la génération des recommandations : {e}")
        return None

# User interface
st.title("Système de Recommandation d'Articles")
st.markdown("---")

# Sidebar for information
with st.sidebar:
    st.header("Informations")

    # API Status
    health = get_health_status(st.session_state.api_url)

    if health.get('status') == 'healthy':
        st.success("API : Connectée")
        st.metric("Nombre d'utilisateurs", health.get('total_users', 0))
        st.metric("Nombre d'articles", health.get('total_articles', 0))
        st.metric("Nombre d'interactions", health.get('total_ratings', 0))
    else:
        st.error("API : Déconnectée")
        st.warning(f"Erreur : {health.get('error', 'Unknown')}")

    st.markdown("---")

    # API Configuration
    st.markdown("### Configuration API")
    new_api_url = st.text_input(
        "URL de l'API :",
        value=st.session_state.api_url,
        help="URL de l'API Azure Functions"
    )

    if st.button("Mettre à jour l'API"):
        st.session_state.api_url = new_api_url.rstrip('/')
        st.session_state.user_ids = []  # Reset user list
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### À propos")
    st.info("Ce système utilise un algorithme de recommandation basé sur le contenu pour suggérer des articles pertinents aux utilisateurs en fonction de leur historique de lecture.")
    st.markdown("**Mode :** API Azure Functions")

# Load users list if not already loaded
if not st.session_state.user_ids:
    with st.spinner("Chargement de la liste des utilisateurs..."):
        users_data = get_users_list(st.session_state.api_url)
        if users_data:
            st.session_state.user_ids = [u['user_id'] for u in users_data]

# Main section
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Obtenir des recommandations")

with col2:
    st.header("Paramètres")

# Random user button outside form
if st.session_state.user_ids:
    if st.button("Utilisateur aléatoire", use_container_width=True):
        st.session_state.random_user_id = int(np.random.choice(st.session_state.user_ids))
else:
    st.warning("Aucun utilisateur chargé. Vérifiez la connexion à l'API.")

# Set default user_id value
if st.session_state.user_ids:
    default_user_id = st.session_state.random_user_id if st.session_state.random_user_id is not None else int(st.session_state.user_ids[0])
    min_user_id = int(min(st.session_state.user_ids))
    max_user_id = int(max(st.session_state.user_ids))
else:
    default_user_id = 1
    min_user_id = 1
    max_user_id = 999999

# Recommendation form
with st.form("reco_form"):
    col1, col2 = st.columns([2, 1])

    with col1:
        # User selection
        user_id_input = st.number_input(
            "ID utilisateur :",
            min_value=min_user_id,
            max_value=max_user_id,
            value=default_user_id,
            step=1,
            help="Entrez l'ID d'un utilisateur pour obtenir des recommandations personnalisées"
        )

    with col2:
        # Number of recommendations
        top_k = st.slider(
            "Nombre de recommandations :",
            min_value=1,
            max_value=20,
            value=5,
            help="Sélectionnez le nombre d'articles à recommander"
        )

    # Submit button
    submitted = st.form_submit_button("Obtenir les recommandations", use_container_width=True, type="primary")

# Display recommendations
if submitted:
    with st.spinner(f"Génération des {top_k} meilleures recommandations..."):
        recommendations = get_recommendations(st.session_state.api_url, user_id_input, n=top_k)

        if recommendations:
            st.success(f"Top {len(recommendations)} articles pour l'utilisateur {user_id_input}")

            # Prepare data for display
            recs_data = []
            for rank, rec in enumerate(recommendations, 1):
                recs_data.append({
                    "Rang": rank,
                    "ID Article": int(rec.get('article_id', 0)),
                    "Score": round(float(rec.get('score', 0)), 4),
                    "Catégorie": rec.get('category_id', 'N/A'),
                    "Nombre de mots": str(rec.get('words_count', 'N/A')),
                })

            # Display table
            df_recs = pd.DataFrame(recs_data)
            st.dataframe(df_recs, use_container_width=True, hide_index=True)

            # Display user statistics
            st.markdown("---")
            st.subheader(f"Statistiques de l'utilisateur {user_id_input}")

            # Get user stats from users list
            users_data = get_users_list(st.session_state.api_url)
            user_stats = next((u for u in users_data if u['user_id'] == user_id_input), None)

            if user_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("ID Utilisateur", user_stats['user_id'])
                with col2:
                    st.metric("Articles consultés", user_stats['n'])
                with col3:
                    st.metric("Note moyenne", round(user_stats['avg_rating'], 2))
            else:
                st.info("Statistiques utilisateur non disponibles")

# Optional: Display users list
if st.session_state.user_ids:
    with st.expander("Voir tous les utilisateurs disponibles (100 premiers)"):
        users_data = get_users_list(st.session_state.api_url)
        if users_data:
            df_users = pd.DataFrame(users_data[:100])
            df_users.columns = ["ID Utilisateur", "Articles consultés", "Note moyenne"]
            st.dataframe(df_users, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: gray;'>
        <small>Application de recommandation d'articles basée sur le contenu</small><br>
        <small>Powered by Azure Functions | API: {st.session_state.api_url}</small>
    </div>
    """,
    unsafe_allow_html=True
)
