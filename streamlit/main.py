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
st.sidebar.markdown("---")

# Statistiques rapides dans la sidebar
try:
    with st.sidebar.expander("📊 Statistiques rapides", expanded=True):
        # Utiliser une requête plus légère pour les statistiques de base
        quick_stats = backend.get_quick_stats()
        
        if quick_stats:
            st.metric("Chansons", f"{quick_stats.get('total_tracks', 0):,}")
            st.metric("Genres", quick_stats.get('total_genres', 0))
            st.metric("Artistes", quick_stats.get('total_artists', 0))
        else:
            st.info("Base de données vide")
            
except Exception as e:
    if "MemoryPoolOutOfMemoryError" in str(e):
        st.sidebar.warning("⚠️ Mémoire limitée - Stats réduites")
    else:
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
        # Récupérer moins de chansons pour éviter les problèmes de mémoire
        popular_songs = backend.get_popular_songs(limit=5)
        
    if popular_songs:
        import pandas as pd
        
        # Préparer l'affichage avec moins de colonnes
        display_data = []
        for song in popular_songs:
            # Limiter les informations affichées
            artists_str = '; '.join(song['artists'][:2])  # Max 2 artistes
            if len(song['artists']) > 2:
                artists_str += f" (+{len(song['artists'])-2} autres)"
                
            display_data.append({
                'Titre': song['name'][:30] + ('...' if len(song['name']) > 30 else ''),
                'Artistes': artists_str,
                'Genre': song.get('genre', 'N/A'),
                'Popularité': song['popularity']
            })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Graphique simple
        st.subheader("📈 Analyse rapide")
        
        # Distribution par genre des top songs (simplifié)
        genre_counts = {}
        for song in popular_songs:
            genre = song.get('genre', 'Inconnu')
            if genre:  # Éviter les genres None
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        if genre_counts:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Répartition par genre (Top 5)**")
                for genre, count in genre_counts.items():
                    percentage = (count / len(popular_songs)) * 100
                    st.write(f"• {genre}: {count} ({percentage:.1f}%)")
            
            with col2:
                # Graphique simple de popularité
                popularity_data = [song['popularity'] for song in popular_songs]
                avg_popularity = sum(popularity_data) / len(popularity_data)
                
                st.write("**Statistiques de popularité**")
                st.write(f"• Moyenne: {avg_popularity:.1f}")
                st.write(f"• Maximum: {max(popularity_data)}")
                st.write(f"• Minimum: {min(popularity_data)}")
    
    else:
        st.info("Aucune donnée à afficher. Commencez par ajouter des chansons!")
        
        if st.button("Importer des données", key="import_data"):
            st.info("Utilisez les scripts d'import dans le dossier 'script' pour charger les données depuis CSV")

except Exception as e:
    if "MemoryPoolOutOfMemoryError" in str(e):
        st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
        st.info("""
        **Solutions possibles:**
        1. Réduire la quantité de données dans la base
        2. Optimiser les requêtes
        3. Passer à un plan Neo4j Aura avec plus de mémoire
        """)
        
        # Affichage minimal en cas d'erreur mémoire
        try:
            count_result = backend.get_simple_count()
            if count_result:
                st.info(f"Base de données contient environ {count_result} chansons")
        except:
            st.info("Impossible d'obtenir le nombre de chansons")
    else:
        st.error(f"Erreur lors du chargement de l'aperçu: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎵 Spotify Neo4j Dashboard - Projet NoSQL</p>
    <p>Powered by Neo4j Aura & Streamlit</p>
</div>
""", unsafe_allow_html=True)
