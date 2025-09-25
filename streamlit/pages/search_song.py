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
                # Limiter encore plus pour éviter les problèmes de mémoire
                results = backend.search_songs(search_query, limit=15)
                
                if results:
                    st.success(f"{len(results)} résultat(s) trouvé(s)")
                    
                    # Afficher les résultats sous forme de tableau optimisé
                    display_data = []
                    for song in results:
                        # Gestion sécurisée des données qui peuvent être None
                        artists = song.get('artists', [])
                        if artists is None:
                            artists = []
                        
                        # S'assurer que artists est une liste
                        if not isinstance(artists, list):
                            artists = [str(artists)] if artists else []
                        
                        artists_str = '; '.join(artists) if artists else 'Inconnu'
                        
                        # Gestion sécurisée des valeurs numériques
                        popularity = song.get('popularity', 0)
                        energy = song.get('energy', 0)
                        danceability = song.get('danceability', 0)
                        
                        # S'assurer que les valeurs numériques ne sont pas None
                        popularity = popularity if popularity is not None else 0
                        energy = energy if energy is not None else 0
                        danceability = danceability if danceability is not None else 0
                        
                        display_data.append({
                            'Titre': song.get('name', 'Sans titre'),
                            'Artistes': artists_str,
                            'Genre': song.get('genre', 'Non spécifié') or 'Non spécifié',
                            'Popularité': popularity,
                            'Énergie': f"{energy:.2f}",
                            'Danceabilité': f"{danceability:.2f}"
                        })
                    
                    df_display = pd.DataFrame(display_data)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Détails d'une chanson sélectionnée
                    st.subheader("Détails")
                    selected_song = st.selectbox(
                        "Sélectionner une chanson pour voir les détails",
                        options=range(len(results)),
                        format_func=lambda i: f"{results[i].get('name', 'Sans titre')} - {'; '.join(results[i].get('artists', []) or [])}"
                    )
                    
                    if selected_song is not None:
                        song = results[selected_song]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            popularity = song.get('popularity', 0) or 0
                            song_id = song.get('id', 'N/A')
                            st.metric("Popularité", popularity)
                            
                        
                        with col2:
                            energy = song.get('energy', 0) or 0
                            danceability = song.get('danceability', 0) or 0
                            st.metric("Energie", f"{energy:.2f}")
                            st.metric("Danceabilité", f"{danceability:.2f}")
                        
                        with col3:
                            st.write("**Artistes:**")
                            artists = song.get('artists', [])
                            if artists and isinstance(artists, list):
                                for artist in artists:
                                    if artist:  # Éviter les artistes None ou vides
                                        st.write(f"• {artist}")
                            else:
                                st.write("• Inconnu")
                            
                            genre = song.get('genre', 'Non spécifié') or 'Non spécifié'
                            st.write(f"**Genre:** {genre}")
                        
                        # Actions sur la chanson
                        st.subheader("Actions")
                        col1, col2 = st.columns(2)
                        
                        song_id = song.get('id', song.get('track_id', 'unknown'))  # Compatibilité
                        
                        with col1:
                            if st.button("✏️ Modifier", key=f"edit_{song_id}"):
                                st.session_state.edit_song = song
                                st.switch_page("pages/edit_song.py")
                        
                        with col2:
                            if st.button("🗑️ Supprimer", key=f"delete_{song_id}"):
                                if st.session_state.get('confirm_delete') == song_id:
                                    result = backend.delete_song(song_id)
                                    if result['success']:
                                        st.success("Chanson supprimée avec succès")
                                        st.rerun()
                                    else:
                                        st.error(result['message'])
                                else:
                                    st.session_state.confirm_delete = song_id
                                    st.warning("Cliquez à nouveau pour confirmer la suppression")
                
                else:
                    st.info("Aucun résultat trouvé pour cette recherche")
                    
            except Exception as e:
                if "MemoryPoolOutOfMemoryError" in str(e):
                    st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
                    st.info("Essayez une recherche plus spécifique ou réduisez le nombre de résultats")
                else:
                    st.error(f"Erreur lors de la recherche: {e}")

elif search_type == "Par genre":
    st.subheader("Recherche par genre")
    
    # Récupérer les genres disponibles
    try:
        genres = backend.get_all_genres()
        
        if genres:
            selected_genre = st.selectbox("Sélectionner un genre", genres)
            limit = st.slider("Nombre de résultats", 5, 25, 15)  # Réduit pour éviter les problèmes de mémoire
            
            if st.button("Rechercher"):
                with st.spinner("Recherche en cours..."):
                    try:
                        results = backend.get_songs_by_genre(selected_genre, limit)
                        
                        if results:
                            st.success(f"{len(results)} chanson(s) trouvée(s) dans le genre '{selected_genre}'")
                            
                            df_results = pd.DataFrame(results)
                            # Colonnes simplifiées pour éviter les erreurs
                            display_data = []
                            for song in results:
                                display_data.append({
                                    'Titre': song['name'][:30] + ('...' if len(song['name']) > 30 else ''),
                                    'Artistes': '; '.join(song.get('artists', [])[:2]),
                                    'Genre': song.get('genre', 'N/A'),
                                    'Popularité': song['popularity']
                                })
                            
                            df_display = pd.DataFrame(display_data)
                            st.dataframe(df_display, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"Aucune chanson trouvée pour le genre '{selected_genre}'")
                    
                    except Exception as e:
                        if "MemoryPoolOutOfMemoryError" in str(e):
                            st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
                            st.info("Réduisez le nombre de résultats demandés")
                        else:
                            st.error(f"Erreur lors de la recherche: {e}")
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
                results = backend.get_songs_by_artist(artist_name, limit=20)  # Ajouter limite
                
                if results:
                    st.success(f"{len(results)} chanson(s) trouvée(s) pour '{artist_name}'")
                    
                    # Affichage simplifié pour éviter les erreurs
                    display_data = []
                    for song in results:
                        display_data.append({
                            'Titre': song['name'][:30] + ('...' if len(song['name']) > 30 else ''),
                            'Artiste': artist_name,
                            'Genre': song.get('genre', 'N/A'),
                            'Popularité': song['popularity']
                        })
                    
                    df_display = pd.DataFrame(display_data)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Aucune chanson trouvée pour l'artiste '{artist_name}'")
                    
            except Exception as e:
                if "MemoryPoolOutOfMemoryError" in str(e):
                    st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
                    st.info(f"L'artiste '{artist_name}' a trop de chansons. Essayez la recherche générale.")
                else:
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
    st.warning("⚠️ Mode optimisé pour économiser la mémoire - Pagination limitée")
    
    # Pagination très limitée
    page_size = st.selectbox("Chansons par page", [10, 15, 20], index=1)  # Très réduit
    page_number = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page_number - 1) * page_size
    
    with st.spinner("Chargement..."):
        try:
            results = backend.get_all_songs(limit=page_size, offset=offset)
            
            if results:
                st.success(f"{len(results)} chanson(s) sur la page {page_number}")
                
                # Affichage simplifié pour éviter les erreurs
                display_data = []
                for song in results:
                    display_data.append({
                        'Titre': song['name'][:30] + ('...' if len(song['name']) > 30 else ''),
                        'Artistes': '; '.join(song.get('artists', [])[:2]),
                        'Genre': song.get('genre', 'N/A'),
                        'Popularité': song['popularity']
                    })
                
                df_display = pd.DataFrame(display_data)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune chanson trouvée sur cette page")
                
        except Exception as e:
            if "MemoryPoolOutOfMemoryError" in str(e):
                st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
                st.info("Réduisez le nombre de chansons par page ou utilisez la recherche spécifique")
            else:
                st.error(f"Erreur lors du chargement: {e}")

# Statistiques rapides
with st.expander("📊 Statistiques rapides"):
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 3 genres")
            genre_stats = backend.get_genre_statistics()[:3]  # Encore plus réduit
            for stat in genre_stats:
                st.text(f"{stat['genre']}: {stat['track_count']} chansons")
        
        with col2:
            st.subheader("Top 3 artistes")
            artist_stats = backend.get_artist_statistics()[:3]  # Encore plus réduit
            for stat in artist_stats:
                st.text(f"{stat['artist']}: {stat['track_count']} chansons")
        
    except Exception as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.info("⚠️ Statistiques désactivées pour économiser la mémoire")
        else:
            st.error(f"Erreur: {e}")