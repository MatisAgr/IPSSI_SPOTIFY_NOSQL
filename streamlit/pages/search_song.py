import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))
from backend import SpotifyBackend

st.title("🔍 Recherche de chansons")

# Initialiser le backend
@st.cache_resource
def get_backend():
    return SpotifyBackend()

try:
    backend = get_backend()
    if not backend.test_connection():
        st.error("Erreur de connexion à la base de données Neo4j")
        st.stop()
except Exception as e:
    st.error(f"Erreur d'initialisation: {e}")
    st.stop()

# Sidebar avec filtres
st.sidebar.header("Filtres de recherche")
search_type = st.sidebar.selectbox(
    "Type de recherche",
    ["Recherche générale", "Par genre", "Par artiste", "Chansons populaires", "Toutes les chansons"]
)

# Interface de recherche selon le type
if search_type == "Recherche générale":
    st.subheader("Recherche par mot-clé")
    search_query = st.text_input(
        'Rechercher une chanson, un artiste, un album ou un genre',
        placeholder="Entrez votre recherche..."
    )
    
    if search_query:
        with st.spinner("Recherche en cours..."):
            try:
                results = backend.search_songs(search_query, limit=50)
                
                if results:
                    st.success(f"{len(results)} résultat(s) trouvé(s)")
                    
                    # Afficher les résultats sous forme de tableau
                    df_results = pd.DataFrame(results)
                    
                    # Colonnes à afficher
                    display_columns = ['name', 'artists', 'album', 'genre', 'popularity', 'duration_ms']
                    
                    # Reformater les données pour l'affichage
                    df_display = df_results[display_columns].copy()
                    df_display['artists'] = df_display['artists'].apply(lambda x: '; '.join(x) if x else 'Inconnu')
                    df_display['duration_ms'] = df_display['duration_ms'].apply(
                        lambda x: f"{x//1000//60}:{(x//1000)%60:02d}" if x else "0:00"
                    )
                    
                    # Renommer les colonnes
                    df_display.columns = ['Titre', 'Artistes', 'Album', 'Genre', 'Popularité', 'Durée']
                    
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Détails d'une chanson sélectionnée
                    st.subheader("Détails")
                    selected_song = st.selectbox(
                        "Sélectionner une chanson pour voir les détails",
                        options=range(len(results)),
                        format_func=lambda i: f"{results[i]['name']} - {'; '.join(results[i]['artists'])}"
                    )
                    
                    if selected_song is not None:
                        song = results[selected_song]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Popularité", song['popularity'])
                            st.metric("Durée", f"{song['duration_ms']//1000//60}:{(song['duration_ms']//1000)%60:02d}")
                            st.metric("Tempo", f"{song.get('tempo', 0):.1f} BPM")
                        
                        with col2:
                            st.metric("Energie", f"{song.get('energy', 0):.2f}")
                            st.metric("Danceabilité", f"{song.get('danceability', 0):.2f}")
                            st.metric("Valence", f"{song.get('valence', 0):.2f}")
                        
                        with col3:
                            st.metric("Acoustique", f"{song.get('acousticness', 0):.2f}")
                            st.metric("Instrumental", f"{song.get('instrumentalness', 0):.2f}")
                            st.metric("Vivacité", f"{song.get('liveness', 0):.2f}")
                        
                        # Actions sur la chanson
                        st.subheader("Actions")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("✏️ Modifier", key=f"edit_{song['track_id']}"):
                                st.session_state.edit_song = song
                                st.switch_page("pages/edit_song.py")
                        
                        with col2:
                            if st.button("🗑️ Supprimer", key=f"delete_{song['track_id']}"):
                                if st.session_state.get('confirm_delete') == song['track_id']:
                                    result = backend.delete_song(song['track_id'])
                                    if result['success']:
                                        st.success("Chanson supprimée avec succès")
                                        st.rerun()
                                    else:
                                        st.error(result['message'])
                                else:
                                    st.session_state.confirm_delete = song['track_id']
                                    st.warning("Cliquez à nouveau pour confirmer la suppression")
                
                else:
                    st.info("Aucun résultat trouvé pour cette recherche")
                    
            except Exception as e:
                st.error(f"Erreur lors de la recherche: {e}")

elif search_type == "Par genre":
    st.subheader("Recherche par genre")
    
    # Récupérer les genres disponibles
    try:
        genres = backend.get_all_genres()
        
        if genres:
            selected_genre = st.selectbox("Sélectionner un genre", genres)
            limit = st.slider("Nombre de résultats", 10, 100, 20)
            
            if st.button("Rechercher"):
                with st.spinner("Recherche en cours..."):
                    results = backend.get_songs_by_genre(selected_genre, limit)
                    
                    if results:
                        st.success(f"{len(results)} chanson(s) trouvée(s) dans le genre '{selected_genre}'")
                        
                        df_results = pd.DataFrame(results)
                        display_columns = ['name', 'artists', 'album', 'popularity']
                        df_display = df_results[display_columns].copy()
                        df_display['artists'] = df_display['artists'].apply(lambda x: '; '.join(x))
                        df_display.columns = ['Titre', 'Artistes', 'Album', 'Popularité']
                        
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Aucune chanson trouvée pour le genre '{selected_genre}'")
        else:
            st.warning("Aucun genre disponible dans la base de données")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des genres: {e}")

elif search_type == "Par artiste":
    st.subheader("Recherche par artiste")
    
    artist_name = st.text_input("Nom de l'artiste")
    
    if artist_name:
        with st.spinner("Recherche en cours..."):
            try:
                results = backend.get_songs_by_artist(artist_name)
                
                if results:
                    st.success(f"{len(results)} chanson(s) trouvée(s) pour '{artist_name}'")
                    
                    df_results = pd.DataFrame(results)
                    display_columns = ['name', 'album', 'genre', 'popularity']
                    df_display = df_results[display_columns].copy()
                    df_display.columns = ['Titre', 'Album', 'Genre', 'Popularité']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Aucune chanson trouvée pour l'artiste '{artist_name}'")
                    
            except Exception as e:
                st.error(f"Erreur lors de la recherche: {e}")

elif search_type == "Chansons populaires":
    st.subheader("Top des chansons populaires")
    
    limit = st.slider("Nombre de chansons", 10, 50, 20)
    
    with st.spinner("Chargement..."):
        try:
            results = backend.get_popular_songs(limit)
            
            if results:
                st.success(f"Top {len(results)} des chansons les plus populaires")
                
                df_results = pd.DataFrame(results)
                display_columns = ['name', 'artists', 'album', 'genre', 'popularity']
                df_display = df_results[display_columns].copy()
                df_display['artists'] = df_display['artists'].apply(lambda x: '; '.join(x))
                df_display.columns = ['Titre', 'Artistes', 'Album', 'Genre', 'Popularité']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune chanson trouvée")
                
        except Exception as e:
            st.error(f"Erreur lors du chargement: {e}")

elif search_type == "Toutes les chansons":
    st.subheader("Toutes les chansons")
    
    # Pagination
    page_size = st.selectbox("Chansons par page", [20, 50, 100], index=1)
    page_number = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page_number - 1) * page_size
    
    with st.spinner("Chargement..."):
        try:
            results = backend.get_all_songs(limit=page_size, offset=offset)
            
            if results:
                st.success(f"{len(results)} chanson(s) sur la page {page_number}")
                
                df_results = pd.DataFrame(results)
                display_columns = ['name', 'artists', 'album', 'genre', 'popularity']
                df_display = df_results[display_columns].copy()
                df_display['artists'] = df_display['artists'].apply(lambda x: '; '.join(x))
                df_display.columns = ['Titre', 'Artistes', 'Album', 'Genre', 'Popularité']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune chanson trouvée sur cette page")
                
        except Exception as e:
            st.error(f"Erreur lors du chargement: {e}")

# Statistiques rapides
with st.expander("📊 Statistiques rapides"):
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 5 genres")
            genre_stats = backend.get_genre_statistics()[:5]
            for stat in genre_stats:
                st.text(f"{stat['genre']}: {stat['track_count']} chansons")
        
        with col2:
            st.subheader("Top 5 artistes")
            artist_stats = backend.get_artist_statistics()[:5]
            for stat in artist_stats:
                st.text(f"{stat['artist']}: {stat['track_count']} chansons")
                
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")