import streamlit as st
import sys
from pathlib import Path

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))
from backend import SpotifyBackend

st.title("Upload a Song")

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

# Formulaire d'upload
with st.form("upload_song_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Informations générales")
        track_name = st.text_input('Nom de la chanson*', help="Nom de la chanson")
        artists = st.text_input('Artiste(s)*', help="Noms des artistes séparés par des points-virgules")
        album_name = st.text_input('Nom de l\'album*')
        track_genre = st.text_input('Genre de la piste*')
        
        st.subheader("Métadonnées")
        popularity = st.number_input('Popularité', min_value=0, max_value=100, value=50)
        duration_ms = st.number_input('Durée (ms)', min_value=1000, value=200000, step=1000)
        explicit = st.selectbox('Explicite', ['Non', 'Oui'])
        
    with col2:
        st.subheader("Caractéristiques audio")
        danceability = st.slider('Danceabilité', 0.0, 1.0, 0.5, step=0.01, format="%.2f")
        energy = st.slider('Energie', 0.0, 1.0, 0.5, step=0.01, format="%.2f")
        key = st.number_input('Clé', min_value=0, max_value=11, value=5)
        loudness = st.slider('Intensité (dB)', -60.0, 0.0, -10.0, step=0.1, format="%.1f")
        mode = st.selectbox('Mode', [0, 1], format_func=lambda x: 'Mineur' if x == 0 else 'Majeur')
        
        speechiness = st.slider('Parole', 0.0, 1.0, 0.1, step=0.01, format="%.2f")
        acousticness = st.slider('Acoustique', 0.0, 1.0, 0.2, step=0.01, format="%.2f")
        instrumentalness = st.slider('Instrumental', 0.0, 1.0, 0.0, step=0.01, format="%.2f")
        liveness = st.slider('Vivacité', 0.0, 1.0, 0.15, step=0.01, format="%.2f")
        valence = st.slider('Valence', 0.0, 1.0, 0.5, step=0.01, format="%.2f")
        tempo = st.number_input('Tempo (BPM)', min_value=60.0, max_value=200.0, value=120.0, step=0.1)
        time_signature = st.number_input('Time Signature', min_value=1, max_value=7, value=4)
    
    # Bouton de soumission
    submitted = st.form_submit_button("Uploader la chanson")
    
    if submitted:
        # Validation des champs obligatoires
        if not all([track_name, artists, album_name, track_genre]):
            st.error("Veuillez remplir tous les champs obligatoires (marqués d'un *)")
        else:
            try:
                # Préparer les données
                song_data = {
                    'track_name': track_name,
                    'artists': artists,
                    'album_name': album_name,
                    'track_genre': track_genre,
                    'popularity': popularity,
                    'duration_ms': duration_ms,
                    'explicit': explicit == 'Oui',
                    'danceability': danceability,
                    'energy': energy,
                    'key': key,
                    'loudness': loudness,
                    'mode': mode,
                    'speechiness': speechiness,
                    'acousticness': acousticness,
                    'instrumentalness': instrumentalness,
                    'liveness': liveness,
                    'valence': valence,
                    'tempo': tempo,
                    'time_signature': time_signature
                }
                
                # Créer la chanson
                result = backend.create_song(song_data)
                
                if result['success']:
                    st.success(result['message'])
                    st.info(f"ID de la chanson: {result['track_id']}")
                    
                    # Afficher un résumé
                    st.subheader("Résumé de la chanson créée")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Popularité", popularity)
                        st.metric("Durée", f"{duration_ms//1000//60}:{(duration_ms//1000)%60:02d}")
                    
                    with col2:
                        st.metric("Energie", f"{energy:.2f}")
                        st.metric("Danceabilité", f"{danceability:.2f}")
                    
                    with col3:
                        st.metric("Valence", f"{valence:.2f}")
                        st.metric("Tempo", f"{tempo} BPM")
                
                else:
                    st.error(f"Erreur lors de l'upload: {result['message']}")
                    
            except Exception as e:
                st.error(f"Erreur lors de l'upload: {str(e)}")

# Afficher les statistiques actuelles
if st.checkbox("Afficher les statistiques de la base"):
    try:
        with st.spinner("Chargement des statistiques..."):
            genre_stats = backend.get_genre_statistics()
            
        st.subheader("Statistiques par genre")
        if genre_stats:
            import pandas as pd
            df_stats = pd.DataFrame(genre_stats[:10])  # Top 10
            st.dataframe(df_stats[['genre', 'track_count', 'avg_popularity']].round(2))
        else:
            st.info("Aucune donnée disponible")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")