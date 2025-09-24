import streamlit as st
import sys
from pathlib import Path

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))
from backend import SpotifyBackend

st.title("✏️ Modifier une chanson")

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

# Vérifier si une chanson est sélectionnée pour l'édition
if 'edit_song' not in st.session_state:
    st.warning("Aucune chanson sélectionnée pour l'édition")
    
    # Interface pour rechercher une chanson à modifier
    st.subheader("Rechercher une chanson à modifier")
    
    search_query = st.text_input("Rechercher par nom de chanson ou artiste")
    
    if search_query:
        try:
            results = backend.search_songs(search_query, limit=20)
            
            if results:
                selected_idx = st.selectbox(
                    "Sélectionner une chanson",
                    options=range(len(results)),
                    format_func=lambda i: f"{results[i]['name']} - {'; '.join(results[i]['artists'])}"
                )
                
                if st.button("Modifier cette chanson"):
                    st.session_state.edit_song = results[selected_idx]
                    st.rerun()
            else:
                st.info("Aucune chanson trouvée")
                
        except Exception as e:
            st.error(f"Erreur de recherche: {e}")
    
    if st.button("← Retour à la recherche"):
        st.switch_page("pages/search_song.py")
    
    st.stop()

# Récupérer la chanson à modifier
song = st.session_state.edit_song

st.info(f"Modification de: **{song['name']}** par {'; '.join(song['artists'])}")

# Formulaire de modification
with st.form("edit_song_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Informations générales")
        track_name = st.text_input('Nom de la chanson', value=song.get('name', ''))
        
        # Afficher les artistes actuels (lecture seule pour simplifier)
        st.text_input('Artistes actuels', value='; '.join(song['artists']), disabled=True)
        st.caption("Pour modifier les artistes, utilisez les opérations avancées")
        
        # Album et genre (lecture seule pour simplifier)
        st.text_input('Album actuel', value=song.get('album', ''), disabled=True)
        st.text_input('Genre actuel', value=song.get('genre', ''), disabled=True)
        
        st.subheader("Métadonnées")
        popularity = st.number_input('Popularité', 
                                   min_value=0, max_value=100, 
                                   value=int(song.get('popularity', 50)))
        
        duration_ms = st.number_input('Durée (ms)', 
                                    min_value=1000, 
                                    value=int(song.get('duration_ms', 200000)), 
                                    step=1000)
        
        explicit = st.selectbox('Explicite', 
                              ['Non', 'Oui'], 
                              index=1 if song.get('explicit', False) else 0)
        
    with col2:
        st.subheader("Caractéristiques audio")
        
        danceability = st.slider('Danceabilité', 0.0, 1.0, 
                               float(song.get('danceability', 0.5)), 
                               step=0.01, format="%.2f")
        
        energy = st.slider('Energie', 0.0, 1.0, 
                         float(song.get('energy', 0.5)), 
                         step=0.01, format="%.2f")
        
        key = st.number_input('Clé', min_value=0, max_value=11, 
                            value=int(song.get('key', 5)))
        
        loudness = st.slider('Intensité (dB)', -60.0, 0.0, 
                           float(song.get('loudness', -10.0)), 
                           step=0.1, format="%.1f")
        
        mode = st.selectbox('Mode', [0, 1], 
                          index=int(song.get('mode', 1)),
                          format_func=lambda x: 'Mineur' if x == 0 else 'Majeur')
        
        speechiness = st.slider('Parole', 0.0, 1.0, 
                              float(song.get('speechiness', 0.1)), 
                              step=0.01, format="%.2f")
        
        acousticness = st.slider('Acoustique', 0.0, 1.0, 
                               float(song.get('acousticness', 0.2)), 
                               step=0.01, format="%.2f")
        
        instrumentalness = st.slider('Instrumental', 0.0, 1.0, 
                                   float(song.get('instrumentalness', 0.0)), 
                                   step=0.01, format="%.2f")
        
        liveness = st.slider('Vivacité', 0.0, 1.0, 
                           float(song.get('liveness', 0.15)), 
                           step=0.01, format="%.2f")
        
        valence = st.slider('Valence', 0.0, 1.0, 
                          float(song.get('valence', 0.5)), 
                          step=0.01, format="%.2f")
        
        tempo = st.number_input('Tempo (BPM)', min_value=60.0, max_value=200.0, 
                              value=float(song.get('tempo', 120.0)), 
                              step=0.1)
        
        time_signature = st.number_input('Time Signature', min_value=1, max_value=7, 
                                       value=int(song.get('time_signature', 4)))
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    
    with col1:
        submitted = st.form_submit_button("💾 Sauvegarder les modifications", type="primary")
    
    with col2:
        if st.form_submit_button("🔄 Réinitialiser"):
            st.rerun()
    
    with col3:
        if st.form_submit_button("❌ Annuler"):
            del st.session_state.edit_song
            st.switch_page("pages/search_song.py")
    
    if submitted:
        if not track_name.strip():
            st.error("Le nom de la chanson ne peut pas être vide")
        else:
            try:
                # Préparer les données de mise à jour
                updates = {
                    'name': track_name,
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
                
                # Effectuer la mise à jour
                result = backend.update_song(song['track_id'], updates)
                
                if result['success']:
                    st.success("Chanson mise à jour avec succès!")
                    
                    # Afficher les modifications
                    st.subheader("Résumé des modifications")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Popularité", popularity, 
                                delta=popularity - int(song.get('popularity', 50)))
                        st.metric("Energie", f"{energy:.2f}", 
                                delta=f"{energy - float(song.get('energy', 0.5)):.2f}")
                    
                    with col2:
                        st.metric("Danceabilité", f"{danceability:.2f}", 
                                delta=f"{danceability - float(song.get('danceability', 0.5)):.2f}")
                        st.metric("Valence", f"{valence:.2f}", 
                                delta=f"{valence - float(song.get('valence', 0.5)):.2f}")
                    
                    with col3:
                        st.metric("Tempo", f"{tempo:.1f} BPM", 
                                delta=f"{tempo - float(song.get('tempo', 120.0)):.1f}")
                        duration_old = int(song.get('duration_ms', 200000))
                        st.metric("Durée", f"{duration_ms//1000//60}:{(duration_ms//1000)%60:02d}",
                                delta=f"{(duration_ms - duration_old)//1000}s")
                    
                    # Mettre à jour la session
                    st.session_state.edit_song.update(updates)
                    
                else:
                    st.error(f"Erreur lors de la mise à jour: {result['message']}")
                    
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour: {str(e)}")

# Informations de débogage
with st.expander("🔧 Informations techniques"):
    st.write("**ID de la chanson:**", song.get('track_id', 'Non disponible'))
    st.write("**Artistes:**", song.get('artists', []))
    st.write("**Album:**", song.get('album', 'Non disponible'))
    st.write("**Genre:**", song.get('genre', 'Non disponible'))

# Actions supplémentaires
st.subheader("Actions supplémentaires")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Voir dans la recherche"):
        del st.session_state.edit_song
        st.switch_page("pages/search_song.py")

with col2:
    if st.button("📊 Voir les statistiques"):
        st.switch_page("pages/analytics.py")

with col3:
    if st.button("🗑️ Supprimer cette chanson"):
        if st.session_state.get('confirm_delete_edit') == song['track_id']:
            try:
                result = backend.delete_song(song['track_id'])
                if result['success']:
                    st.success("Chanson supprimée avec succès")
                    del st.session_state.edit_song
                    if 'confirm_delete_edit' in st.session_state:
                        del st.session_state.confirm_delete_edit
                    st.switch_page("pages/search_song.py")
                else:
                    st.error(result['message'])
            except Exception as e:
                st.error(f"Erreur lors de la suppression: {e}")
        else:
            st.session_state.confirm_delete_edit = song['track_id']
            st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression définitive")