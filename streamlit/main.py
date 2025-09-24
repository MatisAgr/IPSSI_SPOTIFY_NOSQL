import streamlit as st
import sys
from pathlib import Path

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))
from backend import SpotifyBackend

# Configuration de la page
st.set_page_config(
    page_title="Spotify Neo4j Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎵 Spotify Neo4j Dashboard")
st.markdown("### Gestion et analyse de données musicales avec Neo4j")

# Test de connexion
@st.cache_resource
def get_backend():
    return SpotifyBackend()

try:
    backend = get_backend()
    connection_status = backend.test_connection()
    
    if connection_status:
        st.success("✅ Connexion à Neo4j Aura réussie")
    else:
        st.error("❌ Erreur de connexion à Neo4j Aura")
        st.info("Vérifiez votre fichier .env et votre connexion internet")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Erreur d'initialisation: {e}")
    st.stop()

# Sidebar avec navigation
st.sidebar.title("🎵 SPOTIFY DATASET")
st.sidebar.markdown("---")

# Statistiques rapides dans la sidebar
try:
    with st.sidebar.expander("📊 Statistiques rapides", expanded=True):
        genre_stats = backend.get_genre_statistics()
        artist_stats = backend.get_artist_statistics()
        
        if genre_stats and artist_stats:
            total_tracks = sum(stat['track_count'] for stat in genre_stats)
            total_genres = len(genre_stats)
            total_artists = len(artist_stats)
            
            st.metric("Chansons", f"{total_tracks:,}")
            st.metric("Genres", total_genres)
            st.metric("Artistes", total_artists)
        else:
            st.info("Base de données vide")
            
except Exception as e:
    st.sidebar.error("Erreur statistiques")

st.sidebar.markdown("---")

# Navigation principale
st.sidebar.subheader("🔧 Gestion des données")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("➕ Ajouter", use_container_width=True):
        st.switch_page("pages/upload_song.py")

with col2:
    if st.button("🔍 Rechercher", use_container_width=True):
        st.switch_page("pages/search_song.py")

if st.sidebar.button("📊 Analytics", use_container_width=True):
    st.switch_page("pages/analytics.py")

st.sidebar.markdown("---")

# Contenu principal
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📝 Gestion des chansons
    - **Ajouter** de nouvelles chansons
    - **Modifier** les informations existantes
    - **Supprimer** des entrées
    """)
    
    if st.button("Commencer la gestion", key="manage", use_container_width=True):
        st.switch_page("pages/upload_song.py")

with col2:
    st.markdown("""
    ### 🔎 Recherche avancée
    - **Recherche** par mots-clés
    - **Filtrage** par genre/artiste
    - **Tri** par popularité
    """)
    
    if st.button("Lancer une recherche", key="search", use_container_width=True):
        st.switch_page("pages/search_song.py")

with col3:
    st.markdown("""
    ### 📊 Analyses et rapports
    - **Statistiques** par genre
    - **Analyses** de popularité
    - **Corrélations** audio
    """)
    
    if st.button("Voir les analytics", key="analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")

# Aperçu des données
st.markdown("---")
st.subheader("📋 Aperçu des données récentes")

try:
    with st.spinner("Chargement des données..."):
        # Récupérer les chansons les plus populaires
        popular_songs = backend.get_popular_songs(limit=10)
        
    if popular_songs:
        import pandas as pd
        
        df_preview = pd.DataFrame(popular_songs)
        
        # Préparer l'affichage
        display_data = []
        for song in popular_songs:
            display_data.append({
                'Titre': song['name'],
                'Artistes': '; '.join(song['artists']),
                'Genre': song.get('genre', 'N/A'),
                'Popularité': song['popularity'],
                'Énergie': f"{song.get('energy', 0):.2f}",
                'Danceabilité': f"{song.get('danceability', 0):.2f}"
            })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Graphique rapide
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution par genre des top songs
            genre_counts = {}
            for song in popular_songs:
                genre = song.get('genre', 'Inconnu')
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            if genre_counts:
                import plotly.express as px
                fig = px.pie(
                    values=list(genre_counts.values()),
                    names=list(genre_counts.keys()),
                    title="Répartition par genre (Top 10)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Graphique popularité vs énergie
            fig2 = px.scatter(
                df_preview,
                x='energy',
                y='popularity',
                size='danceability',
                hover_name='name',
                title="Popularité vs Énergie"
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.info("Aucune donnée à afficher. Commencez par ajouter des chansons!")
        
        if st.button("Importer des données", key="import_data"):
            st.info("Utilisez les scripts d'import dans le dossier 'script' pour charger les données depuis CSV")

except Exception as e:
    st.error(f"Erreur lors du chargement de l'aperçu: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎵 Spotify Neo4j Dashboard - Projet NoSQL</p>
    <p>Powered by Neo4j Aura & Streamlit</p>
</div>
""", unsafe_allow_html=True)
