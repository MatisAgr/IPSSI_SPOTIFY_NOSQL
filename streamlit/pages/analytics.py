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
                'Genre', 'Nb Chansons', 'Pop. Moy.', 'Énergie Moy.', 
                'Dance. Moy.', 'Valence Moy.', 'Pop. Min', 'Pop. Max'
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
                most_followers = df_artists.dropna(subset=['followers'])
                if not most_followers.empty:
                    top_followers = most_followers.loc[most_followers['followers'].idxmax()]
                    st.metric("Plus de followers", 
                             top_followers['artist'],
                             f"{top_followers['followers']:,}")
            
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
        # Récupérer un échantillon de chansons pour l'analyse
        sample_songs = backend.get_all_songs(limit=1000)
        
        if sample_songs:
            df_audio = pd.DataFrame(sample_songs)
            
            # Sélectionner les caractéristiques audio
            audio_features = ['danceability', 'energy', 'loudness', 'speechiness', 
                            'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
            
            # Statistiques descriptives
            st.subheader("Statistiques descriptives")
            
            audio_df = df_audio[audio_features].describe()
            st.dataframe(audio_df.round(3), use_container_width=True)
            
            # Histogrammes
            st.subheader("Distribution des caractéristiques audio")
            
            feature_to_analyze = st.selectbox(
                "Choisir une caractéristique",
                audio_features
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(df_audio, 
                                      x=feature_to_analyze,
                                      nbins=30,
                                      title=f"Distribution de {feature_to_analyze}")
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                fig_box = px.box(df_audio,
                               y=feature_to_analyze,
                               title=f"Box plot de {feature_to_analyze}")
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Matrice de corrélation
            st.subheader("Matrice de corrélation")
            
            corr_matrix = df_audio[audio_features].corr()
            
            fig_corr = px.imshow(corr_matrix,
                               text_auto=True,
                               aspect="auto",
                               color_continuous_scale='RdBu',
                               title="Corrélations entre caractéristiques audio")
            
            st.plotly_chart(fig_corr, use_container_width=True)
        
        else:
            st.warning("Aucune donnée disponible pour l'analyse audio")
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse audio: {e}")

elif analysis_type == "Corrélations":
    st.header("📊 Analyse des Corrélations Avancées")
    
    try:
        # Récupérer les données
        songs_data = backend.get_all_songs(limit=2000)
        
        if songs_data:
            df = pd.DataFrame(songs_data)
            
            # Sélectionner les variables numériques
            numeric_cols = ['popularity', 'duration_ms', 'danceability', 'energy', 
                          'key', 'loudness', 'speechiness', 'acousticness', 
                          'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']
            
            numeric_data = df[numeric_cols].select_dtypes(include=[float, int])
            
            # Analyse par paires de variables
            st.subheader("Analyse par paires")
            
            col1, col2 = st.columns(2)
            
            with col1:
                var1 = st.selectbox("Variable X", numeric_cols, index=0)
            
            with col2:
                var2 = st.selectbox("Variable Y", numeric_cols, index=1)
            
            if var1 != var2:
                fig_scatter = px.scatter(df,
                                       x=var1,
                                       y=var2,
                                       color='genre' if 'genre' in df.columns else None,
                                       title=f"Relation entre {var1} et {var2}")
                
                # Ajouter ligne de tendance
                fig_scatter.update_traces(opacity=0.6)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Calculer la corrélation
                correlation = numeric_data[var1].corr(numeric_data[var2])
                
                if abs(correlation) > 0.7:
                    level = "Très forte"
                    color = "red"
                elif abs(correlation) > 0.5:
                    level = "Forte"
                    color = "orange"
                elif abs(correlation) > 0.3:
                    level = "Modérée"
                    color = "yellow"
                else:
                    level = "Faible"
                    color = "green"
                
                st.markdown(f"**Corrélation:** ::{color}[{correlation:.3f}] ({level})")
            
            # Heatmap complète
            st.subheader("Matrice de corrélation complète")
            
            corr_full = numeric_data.corr()
            
            fig_heatmap = px.imshow(corr_full,
                                  text_auto=True,
                                  aspect="auto",
                                  color_continuous_scale='RdBu',
                                  color_continuous_midpoint=0,
                                  title="Matrice de corrélation complète")
            
            fig_heatmap.update_layout(width=800, height=800)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Top corrélations
            st.subheader("Top corrélations")
            
            # Créer une liste des corrélations triées
            corr_pairs = []
            for i in range(len(corr_full.columns)):
                for j in range(i+1, len(corr_full.columns)):
                    var_i = corr_full.columns[i]
                    var_j = corr_full.columns[j]
                    corr_val = corr_full.iloc[i, j]
                    corr_pairs.append((var_i, var_j, corr_val))
            
            # Trier par valeur absolue de corrélation
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Corrélations positives les plus fortes:**")
                positive_corr = [x for x in corr_pairs if x[2] > 0][:10]
                for var1, var2, corr in positive_corr:
                    st.write(f"{var1} ↔ {var2}: **{corr:.3f}**")
            
            with col2:
                st.write("**Corrélations négatives les plus fortes:**")
                negative_corr = [x for x in corr_pairs if x[2] < 0][:10]
                for var1, var2, corr in negative_corr:
                    st.write(f"{var1} ↔ {var2}: **{corr:.3f}**")
        
        else:
            st.warning("Données insuffisantes pour l'analyse de corrélation")
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse de corrélation: {e}")

# Bouton de retour
if st.button("← Retour au menu principal"):
    st.switch_page("main.py")