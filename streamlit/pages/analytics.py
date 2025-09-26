import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))
from backend import SpotifyBackend

st.title("📊 Analytics et Statistiques")

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

# Sidebar pour sélection des analyses
st.sidebar.header("Types d'analyses")
analysis_type = st.sidebar.selectbox(
    "Choisir une analyse",
    [
        "Vue d'ensemble", 
        "Statistiques par Genre", 
        "Statistiques par Artiste",
        "Analyse de Popularité",
        "Caractéristiques Audio",
        "Corrélations"
    ]
)

if analysis_type == "Vue d'ensemble":
    st.header("Vue d'ensemble de la base de données")
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        # Statistiques générales
        genre_stats = backend.get_genre_statistics()
        artist_stats = backend.get_artist_statistics()
        
        total_tracks = sum(stat['track_count'] for stat in genre_stats)
        total_genres = len(genre_stats)
        total_artists = len(artist_stats)
        
        if genre_stats:
            avg_popularity = sum(stat['avg_popularity'] * stat['track_count'] for stat in genre_stats) / total_tracks
        else:
            avg_popularity = 0
        
        with col1:
            st.metric("Total Chansons", f"{total_tracks:,}")
        
        with col2:
            st.metric("Total Genres", total_genres)
        
        with col3:
            st.metric("Total Artistes", total_artists)
        
        with col4:
            st.metric("Popularité Moyenne", f"{avg_popularity:.1f}")
        
        # Graphiques de vue d'ensemble
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 10 Genres")
            if genre_stats:
                df_genres = pd.DataFrame(genre_stats[:10])
                fig_genres = px.pie(df_genres, 
                                  values='track_count', 
                                  names='genre',
                                  title="Répartition par Genre")
                st.plotly_chart(fig_genres, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Artistes")
            if artist_stats:
                df_artists = pd.DataFrame(artist_stats[:10])
                fig_artists = px.bar(df_artists,
                                   x='track_count',
                                   y='artist',
                                   orientation='h',
                                   title="Nombre de Chansons par Artiste")
                fig_artists.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_artists, use_container_width=True)
    
    except Exception as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
            st.info("Essayez de réduire la quantité de données ou utilisez les statistiques rapides")
        else:
            st.error(f"Erreur lors du chargement de la vue d'ensemble: {e}")

elif analysis_type == "Statistiques par Genre":
    st.header("📈 Analyse par Genre (GROUP BY)")
    
    try:
        with st.spinner("Chargement des statistiques par genre..."):
            genre_stats = backend.get_genre_statistics()
        
        if genre_stats:
            df_genres = pd.DataFrame(genre_stats)
            
            # Métriques principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                top_genre = df_genres.iloc[0]
                st.metric("Genre le plus populaire", 
                         top_genre['genre'], 
                         f"{top_genre['track_count']} chansons")
            
            with col2:
                highest_avg_pop = df_genres.loc[df_genres['avg_popularity'].idxmax()]
                st.metric("Meilleure popularité moyenne", 
                         highest_avg_pop['genre'],
                         f"{highest_avg_pop['avg_popularity']:.1f}")
            
            with col3:
                most_energetic = df_genres.loc[df_genres['avg_energy'].idxmax()]
                st.metric("Genre le plus énergique", 
                         most_energetic['genre'],
                         f"{most_energetic['avg_energy']:.2f}")
            
            # Tableau détaillé
            st.subheader("Statistiques détaillées par genre")
            
            # Formater le dataframe pour l'affichage
            df_display = df_genres.copy()
            df_display = df_display.round(2)
            df_display.columns = [
                'Genre', 'Nb Chansons', 'Pop. Moy.', 'Énergie Moy.', 'Dance. Moy.'
            ]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Nombre de chansons par genre")
                fig_count = px.bar(df_genres[:15], 
                                 x='genre', y='track_count',
                                 title="Distribution des chansons")
                fig_count.update_xaxes(tickangle=45)
                st.plotly_chart(fig_count, use_container_width=True)
            
            with col2:
                st.subheader("Popularité moyenne par genre")
                fig_pop = px.bar(df_genres[:15], 
                               x='genre', y='avg_popularity',
                               color='avg_popularity',
                               color_continuous_scale='viridis',
                               title="Popularité par genre")
                fig_pop.update_xaxes(tickangle=45)
                st.plotly_chart(fig_pop, use_container_width=True)
            
            # Scatter plot avancé
            st.subheader("Analyse multidimensionnelle")
            fig_scatter = px.scatter(df_genres,
                                   x='avg_energy',
                                   y='avg_popularity',
                                   size='track_count',
                                   color='avg_danceability',
                                   hover_name='genre',
                                   title="Énergie vs Popularité (taille = nb chansons, couleur = danceabilité)",
                                   labels={
                                       'avg_energy': 'Énergie Moyenne',
                                       'avg_popularity': 'Popularité Moyenne'
                                   })
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        else:
            st.warning("Aucune donnée de genre disponible")
    
    except Exception as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
            st.info("Analyse des genres réduite pour économiser la mémoire")
        else:
            st.error(f"Erreur lors de l'analyse par genre: {e}")

elif analysis_type == "Statistiques par Artiste":
    st.header("🎤 Analyse par Artiste")
    
    try:
        with st.spinner("Chargement des statistiques par artiste..."):
            artist_stats = backend.get_artist_statistics()
        
        if artist_stats:
            df_artists = pd.DataFrame(artist_stats)
            
            # Métriques
            col1, col2, col3 = st.columns(3)
            
            with col1:
                top_artist = df_artists.iloc[0]
                st.metric("Artiste le plus prolifique", 
                         top_artist['artist'],
                         f"{top_artist['track_count']} chansons")
            
            with col2:
                most_popular = df_artists.loc[df_artists['avg_popularity'].idxmax()]
                st.metric("Artiste le plus populaire", 
                         most_popular['artist'],
                         f"{most_popular['avg_popularity']:.1f}")
            
            with col3:
                # Remplacer followers par une métrique basée sur les données disponibles
                if len(df_artists) > 0:
                    total_tracks = df_artists['track_count'].sum()
                    st.metric("Total chansons DB", 
                             f"{total_tracks:,}",
                             f"{len(df_artists)} artistes")
            
            # Top artistes
            st.subheader("Top 20 artistes par nombre de chansons")
            
            fig_artists = px.bar(df_artists[:20],
                               x='track_count',
                               y='artist',
                               orientation='h',
                               color='avg_popularity',
                               color_continuous_scale='plasma',
                               title="Nombre de chansons (couleur = popularité)")
            fig_artists.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=600
            )
            st.plotly_chart(fig_artists, use_container_width=True)
            
            # Relation popularité vs nombre de chansons
            st.subheader("Relation Popularité vs Productivité")
            fig_rel = px.scatter(df_artists,
                               x='track_count',
                               y='avg_popularity',
                               hover_name='artist',
                               title="Popularité vs Nombre de chansons",
                               labels={
                                   'track_count': 'Nombre de chansons',
                                   'avg_popularity': 'Popularité moyenne'
                               })
            
            # Ajouter une ligne de tendance
            import numpy as np
            z = np.polyfit(df_artists['track_count'], df_artists['avg_popularity'], 1)
            p = np.poly1d(z)
            fig_rel.add_traces(go.Scatter(
                x=df_artists['track_count'],
                y=p(df_artists['track_count']),
                mode='lines',
                name='Tendance',
                line=dict(color='red', dash='dash')
            ))
            
            st.plotly_chart(fig_rel, use_container_width=True)
            
            # Tableau détaillé
            st.subheader("Statistiques détaillées")
            df_display = df_artists.copy().round(2)
            df_display.columns = ['Artiste', 'Nb Chansons', 'Pop. Moyenne', 'Followers']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        else:
            st.warning("Aucune donnée d'artiste disponible")
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse par artiste: {e}")

elif analysis_type == "Analyse de Popularité":
    st.header("⭐ Analyse de la Popularité")
    
    try:
        # Récupérer les chansons populaires et les statistiques
        popular_songs = backend.get_popular_songs(50)
        genre_stats = backend.get_genre_statistics()
        
        if popular_songs and genre_stats:
            df_popular = pd.DataFrame(popular_songs)
            df_genres = pd.DataFrame(genre_stats)
            
            # Distribution de popularité
            st.subheader("Distribution de la popularité par genre")
            
            # Créer des bins de popularité
            df_genres['popularity_category'] = pd.cut(
                df_genres['avg_popularity'], 
                bins=[0, 30, 50, 70, 100], 
                labels=['Faible', 'Moyenne', 'Élevée', 'Très élevée']
            )
            
            pop_dist = df_genres['popularity_category'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(values=pop_dist.values, 
                               names=pop_dist.index,
                               title="Répartition des niveaux de popularité")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Top chansons populaires
                st.subheader("Top 10 chansons populaires")
                for i, song in enumerate(df_popular[:10].to_dict('records')):
                    with st.expander(f"{i+1}. {song['name']} - {song['popularity']}★"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Artistes:** {'; '.join(song['artists'])}")
                            st.write(f"**Album:** {song.get('album', 'N/A')}")
                        with col_b:
                            st.write(f"**Genre:** {song.get('genre', 'N/A')}")
                            st.write(f"**Énergie:** {song.get('energy', 0):.2f}")
            
            # Analyse des facteurs de popularité
            st.subheader("Facteurs influençant la popularité")
            
            # Corrélation avec les caractéristiques audio
            audio_features = ['energy', 'danceability', 'valence', 'acousticness', 'liveness']
            correlations = {}
            
            for feature in audio_features:
                if feature in df_popular.columns:
                    corr = df_popular['popularity'].corr(df_popular[feature])
                    correlations[feature] = corr
            
            if correlations:
                df_corr = pd.DataFrame(list(correlations.items()), 
                                     columns=['Caractéristique', 'Corrélation'])
                df_corr = df_corr.sort_values('Corrélation', key=abs, ascending=False)
                
                fig_corr = px.bar(df_corr,
                                x='Corrélation',
                                y='Caractéristique',
                                orientation='h',
                                color='Corrélation',
                                color_continuous_scale='RdYlBu',
                                title="Corrélation avec la popularité")
                
                st.plotly_chart(fig_corr, use_container_width=True)
        
        else:
            st.warning("Données insuffisantes pour l'analyse de popularité")
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse de popularité: {e}")

elif analysis_type == "Caractéristiques Audio":
    st.header("🎵 Analyse des Caractéristiques Audio")
    
    try:
        # Utiliser un petit échantillon pour éviter les problèmes de mémoire
        sample_songs = backend.get_popular_songs(limit=50)  # Réduire drastiquement
        
        if sample_songs:
            df_audio = pd.DataFrame(sample_songs)
            
            # Sélectionner seulement les caractéristiques audio principales
            audio_features = ['danceability', 'energy', 'valence']  # Réduire le nombre
            
            # Vérifier que les colonnes existent
            available_features = [f for f in audio_features if f in df_audio.columns]
            
            if available_features:
                # Statistiques descriptives simplifiées
                st.subheader("Statistiques descriptives (échantillon de 50 chansons)")
                
                audio_df = df_audio[available_features].describe()
                st.dataframe(audio_df.round(3), use_container_width=True)
                
                # Un seul graphique pour éviter la surcharge
                st.subheader("Distribution des caractéristiques audio")
                
                feature_to_analyze = st.selectbox(
                    "Choisir une caractéristique",
                    available_features
                )
                
                # Graphique simple sans plotly pour économiser la mémoire
                st.bar_chart(df_audio[feature_to_analyze].value_counts().head(10))
                
                # Statistiques textuelles au lieu de matrice complexe
                st.subheader("Analyse des caractéristiques")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Danceabilité moyenne", f"{df_audio['danceability'].mean():.2f}")
                
                with col2:
                    st.metric("Énergie moyenne", f"{df_audio['energy'].mean():.2f}")
                
                with col3:
                    st.metric("Valence moyenne", f"{df_audio['valence'].mean():.2f}")
            else:
                st.warning("Caractéristiques audio non disponibles dans les données")
        else:
            st.warning("Aucune donnée disponible")
    
    except Exception as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
            st.info("Analyse audio désactivée pour économiser la mémoire")
        else:
            st.error(f"Erreur lors de l'analyse audio: {e}")

elif analysis_type == "Corrélations":
    st.header("📊 Analyse des Corrélations Simplifiée")
    
    try:
        # Utiliser un échantillon très réduit pour éviter les problèmes de mémoire
        songs_data = backend.get_popular_songs(limit=30)  # Très réduit
        
        if songs_data:
            df = pd.DataFrame(songs_data)
            
            # Sélectionner seulement les variables principales
            numeric_cols = ['popularity', 'danceability', 'energy', 'valence']
            
            # Vérifier que les colonnes existent
            available_cols = [col for col in numeric_cols if col in df.columns]
            
            if len(available_cols) >= 2:
                numeric_data = df[available_cols]
                
                st.subheader("Matrice de corrélation simplifiée")
                
                # Calculer la corrélation de manière simple
                corr_results = []
                for i, col1 in enumerate(available_cols):
                    for j, col2 in enumerate(available_cols):
                        if i < j:  # Éviter les doublons
                            try:
                                corr_val = df[col1].corr(df[col2])
                                if not pd.isna(corr_val):
                                    corr_results.append({
                                        'Variable 1': col1,
                                        'Variable 2': col2,
                                        'Corrélation': round(corr_val, 3)
                                    })
                            except:
                                continue
                
                if corr_results:
                    corr_df = pd.DataFrame(corr_results)
                    corr_df = corr_df.sort_values('Corrélation', key=abs, ascending=False)
                    
                    st.dataframe(corr_df, use_container_width=True, hide_index=True)
                    
                    # Affichage textuel des corrélations les plus fortes
                    if len(corr_results) > 0:
                        strongest = corr_results[0]
                        st.info(f"🔗 Corrélation la plus forte: **{strongest['Variable 1']}** ↔ **{strongest['Variable 2']}** ({strongest['Corrélation']})")
                else:
                    st.warning("Impossible de calculer les corrélations")
            else:
                st.warning("Données insuffisantes pour l'analyse de corrélation")
        else:
            st.warning("Aucune donnée disponible")
    
    except Exception as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.error("⚠️ Mémoire insuffisante dans Neo4j Aura")
            st.info("Analyse de corrélation désactivée pour économiser la mémoire")
        else:
            st.error(f"Erreur lors de l'analyse de corrélation: {e}")

# Bouton de retour
if st.button("← Retour au menu principal"):
    st.switch_page("main.py")