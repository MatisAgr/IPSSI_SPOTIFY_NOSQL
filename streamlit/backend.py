import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
import pandas as pd
import uuid
from typing import Optional, List, Dict, Any

# Charger les variables d'environnement
load_dotenv()

class SpotifyBackend:
    """Backend pour les opérations CRUD Spotify avec Neo4j"""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Configuration Neo4j manquante dans .env")
        
        self.driver = GraphDatabase.driver(
            self.uri, 
            auth=(self.username, self.password),
            database=self.database
        )
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def test_connection(self) -> bool:
        """Test la connexion à Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
                return True
        except Exception:
            return False
    
    # ==================== CREATE OPERATIONS ====================
    
    def create_song(self, song_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle chanson avec toutes ses relations
        
        Args:
            song_data: Dictionnaire contenant les données de la chanson
        
        Returns:
            Résultat de la création avec l'ID généré
        """
        # Générer un ID unique si pas fourni
        if 'track_id' not in song_data or not song_data['track_id']:
            song_data['track_id'] = str(uuid.uuid4())
        
        with self.driver.session() as session:
            query = """
            // Créer ou récupérer le genre
            MERGE (g:Genre {name: $genre})
            
            // Créer ou récupérer l'album
            MERGE (al:Album {name: $album_name})
            
            // Créer la nouvelle track
            CREATE (t:Track {
                track_id: $track_id,
                name: $track_name,
                popularity: $popularity,
                duration_ms: $duration_ms,
                explicit: $explicit,
                danceability: $danceability,
                energy: $energy,
                key: $key,
                loudness: $loudness,
                mode: $mode,
                speechiness: $speechiness,
                acousticness: $acousticness,
                instrumentalness: $instrumentalness,
                liveness: $liveness,
                valence: $valence,
                tempo: $tempo,
                time_signature: $time_signature
            })
            
            // Créer les relations
            MERGE (t)-[:BELONGS_TO]->(al)
            MERGE (t)-[:HAS_GENRE]->(g)
            
            // Traiter les artistes
            WITH t, al, g, $artists as artists_list
            UNWIND artists_list as artist_name
            WITH t, al, g, artist_name WHERE artist_name <> ""
            MERGE (a:Artist {name: artist_name})
            MERGE (a)-[:PERFORMS]->(t)
            MERGE (a)-[:CREATED]->(al)
            
            RETURN t.track_id as created_id
            """
            
            # Nettoyer et valider les données
            artists_list = song_data.get('artists', [])
            if isinstance(artists_list, str):
                artists_list = [artist.strip() for artist in artists_list.split(';') if artist.strip()]
            
            params = {
                'track_id': song_data['track_id'],
                'track_name': song_data.get('track_name', ''),
                'album_name': song_data.get('album_name', ''),
                'genre': song_data.get('track_genre', ''),
                'artists': artists_list,
                'popularity': int(song_data.get('popularity', 0)),
                'duration_ms': int(song_data.get('duration_ms', 0)),
                'explicit': bool(song_data.get('explicit', False)),
                'danceability': float(song_data.get('danceability', 0.0)),
                'energy': float(song_data.get('energy', 0.0)),
                'key': int(song_data.get('key', 0)),
                'loudness': float(song_data.get('loudness', 0.0)),
                'mode': int(song_data.get('mode', 0)),
                'speechiness': float(song_data.get('speechiness', 0.0)),
                'acousticness': float(song_data.get('acousticness', 0.0)),
                'instrumentalness': float(song_data.get('instrumentalness', 0.0)),
                'liveness': float(song_data.get('liveness', 0.0)),
                'valence': float(song_data.get('valence', 0.0)),
                'tempo': float(song_data.get('tempo', 0.0)),
                'time_signature': int(song_data.get('time_signature', 4))
            }
            
            result = session.run(query, **params)
            record = result.single()
            
            return {
                'success': True,
                'track_id': record['created_id'],
                'message': f"Chanson '{song_data.get('track_name')}' créée avec succès"
            }
    
    def create_artist(self, name: str, followers: Optional[int] = None) -> Dict[str, Any]:
        """Crée un nouvel artiste"""
        with self.driver.session() as session:
            query = """
            MERGE (a:Artist {name: $name})
            ON CREATE SET a.followers = $followers
            ON MATCH SET a.followers = COALESCE($followers, a.followers)
            RETURN a
            """
            result = session.run(query, name=name, followers=followers)
            record = result.single()
            
            if record:
                return {
                    'success': True,
                    'artist': dict(record['a']),
                    'message': f"Artiste '{name}' créé avec succès"
                }
            else:
                return {'success': False, 'message': "Erreur lors de la création"}
    
    def create_album(self, name: str, release_date: Optional[str] = None) -> Dict[str, Any]:
        """Crée un nouvel album"""
        with self.driver.session() as session:
            query = """
            MERGE (al:Album {name: $name})
            ON CREATE SET al.release_date = $release_date
            ON MATCH SET al.release_date = COALESCE($release_date, al.release_date)
            RETURN al
            """
            result = session.run(query, name=name, release_date=release_date)
            record = result.single()
            
            if record:
                return {
                    'success': True,
                    'album': dict(record['al']),
                    'message': f"Album '{name}' créé avec succès"
                }
            else:
                return {'success': False, 'message': "Erreur lors de la création"}
    
    # ==================== READ OPERATIONS ====================
    
    def search_songs(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des chansons par nom, artiste ou album - Version optimisée mémoire
        
        Args:
            search_term: Terme de recherche
            limit: Nombre maximum de résultats (max 25 pour éviter problèmes mémoire)
        
        Returns:
            Liste des chansons trouvées avec leurs détails
        """
        # Forcer une limite basse pour éviter les problèmes de mémoire
        safe_limit = min(limit, 25)
        
        with self.driver.session() as session:
            cypher_query = """
            MATCH (t:Track)
            OPTIONAL MATCH (a:Artist)-[:PERFORMS]->(t)
            OPTIONAL MATCH (t)-[:HAS_GENRE]->(g:Genre)
            
            WHERE toLower(t.name) CONTAINS toLower($search_term)
               OR toLower(a.name) CONTAINS toLower($search_term)
               OR toLower(g.name) CONTAINS toLower($search_term)
            
            WITH t, 
                 collect(DISTINCT a.name)[..2] as artists_limited,  // Max 2 artistes
                 g.name as genre
            
            RETURN {
                id: t.id,
                name: t.name,
                popularity: t.popularity,
                energy: t.energy,
                danceability: t.danceability
            } as track,
            artists_limited as artists,
            genre
            ORDER BY t.popularity DESC
            LIMIT $limit
            """
            
            result = session.run(cypher_query, search_term=search_term, limit=safe_limit)
            
            songs = []
            for record in result:
                track = dict(record['track'])
                track['artists'] = record['artists'] or []
                track['genre'] = record['genre']
                songs.append(track)
            
            return songs
    
    def get_song_by_id(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une chanson par son ID avec tous ses détails"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Track {track_id: $track_id})
            OPTIONAL MATCH (a:Artist)-[:PERFORMS]->(t)
            OPTIONAL MATCH (t)-[:BELONGS_TO]->(al:Album)
            OPTIONAL MATCH (t)-[:HAS_GENRE]->(g:Genre)
            
            RETURN t,
                   collect(DISTINCT a.name) as artists,
                   al.name as album,
                   g.name as genre
            """
            
            result = session.run(query, track_id=track_id)
            record = result.single()
            
            if record:
                track = dict(record['t'])
                track['artists'] = record['artists']
                track['album'] = record['album']
                track['genre'] = record['genre']
                return track
            
            return None
    
    def get_all_songs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère toutes les chansons avec pagination - Version optimisée mémoire"""
        # Forcer des limites très basses pour éviter les problèmes de mémoire
        safe_limit = min(limit, 20)  # Max 20 chansons à la fois
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Track)
            OPTIONAL MATCH (a:Artist)-[:PERFORMS]->(t)
            OPTIONAL MATCH (t)-[:HAS_GENRE]->(g:Genre)
            
            WITH t, 
                 collect(DISTINCT a.name)[..2] as artists_limited,  // Max 2 artistes
                 g.name as genre
            
            RETURN {
                id: t.id,
                name: t.name,
                popularity: t.popularity,
                energy: t.energy,
                danceability: t.danceability
            } as track,
            artists_limited as artists,
            genre
            ORDER BY t.popularity DESC
            SKIP $offset
            LIMIT $limit
            """
            
            result = session.run(query, limit=safe_limit, offset=offset)
            
            songs = []
            for record in result:
                track = dict(record['track'])
                track['artists'] = record['artists'] or []
                track['genre'] = record['genre']
                songs.append(track)
            
            return songs
    
    def get_songs_by_genre(self, genre: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les chansons d'un genre spécifique - Version optimisée mémoire"""
        # Forcer une limite basse pour éviter les problèmes de mémoire
        safe_limit = min(limit, 30)
        
        with self.driver.session() as session:
            query = """
            MATCH (g:Genre {name: $genre})<-[:HAS_GENRE]-(t:Track)
            OPTIONAL MATCH (a:Artist)-[:PERFORMS]->(t)
            
            WITH t, collect(DISTINCT a.name)[..2] as artists_limited, g.name as genre
            
            RETURN {
                id: t.id,
                name: t.name,
                popularity: t.popularity,
                energy: t.energy,
                danceability: t.danceability
            } as track,
            artists_limited as artists,
            genre
            ORDER BY t.popularity DESC
            LIMIT $limit
            """
            
            result = session.run(query, genre=genre, limit=safe_limit)
            
            songs = []
            for record in result:
                track = dict(record['track'])
                track['artists'] = record['artists'] or []
                track['genre'] = record['genre']
                songs.append(track)
            
            return songs
    
    def get_songs_by_artist(self, artist_name: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Récupère les chansons d'un artiste - Version optimisée mémoire"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Artist {name: $artist_name})-[:PERFORMS]->(t:Track)
            OPTIONAL MATCH (t)-[:HAS_GENRE]->(g:Genre)
            
            RETURN {
                id: t.id,
                name: t.name,
                popularity: t.popularity,
                energy: t.energy,
                danceability: t.danceability
            } as track,
            [a.name] as artists,
            g.name as genre
            ORDER BY t.popularity DESC
            LIMIT $limit
            """
            
            result = session.run(query, artist_name=artist_name, limit=limit)
            
            songs = []
            for record in result:
                track = dict(record['track'])
                track['artists'] = record['artists']
                track['genre'] = record['genre']
                songs.append(track)
            
            return songs
    
    def get_all_artists(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère tous les artistes"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Artist)
            OPTIONAL MATCH (a)-[:PERFORMS]->(t:Track)
            RETURN a.name as name, 
                   a.followers as followers,
                   count(t) as track_count
            ORDER BY track_count DESC, a.name
            LIMIT $limit
            """
            
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def get_all_genres(self) -> List[str]:
        """Récupère tous les genres disponibles"""
        with self.driver.session() as session:
            query = """
            MATCH (g:Genre)
            RETURN g.name as name
            ORDER BY g.name
            """
            
            result = session.run(query)
            return [record['name'] for record in result]
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_song(self, track_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une chanson existante"""
        with self.driver.session() as session:
            # Construire la requête de mise à jour dynamiquement
            set_clauses = []
            params = {'track_id': track_id}
            
            for key, value in updates.items():
                if key not in ['track_id', 'artists', 'album', 'genre']:  # Exclure les champs spéciaux
                    set_clauses.append(f"t.{key} = ${key}")
                    params[key] = value
            
            if not set_clauses:
                return {'success': False, 'message': 'Aucune mise à jour fournie'}
            
            query = f"""
            MATCH (t:Track {{track_id: $track_id}})
            SET {', '.join(set_clauses)}
            RETURN t
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if record:
                return {
                    'success': True,
                    'track': dict(record['t']),
                    'message': 'Chanson mise à jour avec succès'
                }
            else:
                return {'success': False, 'message': 'Chanson non trouvée'}
    
    def update_artist(self, artist_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un artiste"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Artist {name: $artist_name})
            SET a.followers = COALESCE($followers, a.followers)
            RETURN a
            """
            
            result = session.run(query, 
                               artist_name=artist_name, 
                               followers=updates.get('followers'))
            record = result.single()
            
            if record:
                return {
                    'success': True,
                    'artist': dict(record['a']),
                    'message': 'Artiste mis à jour avec succès'
                }
            else:
                return {'success': False, 'message': 'Artiste non trouvé'}
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete_song(self, track_id: str) -> Dict[str, Any]:
        """Supprime une chanson et ses relations"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Track {track_id: $track_id})
            DETACH DELETE t
            RETURN count(t) as deleted_count
            """
            
            result = session.run(query, track_id=track_id)
            deleted_count = result.single()['deleted_count']
            
            if deleted_count > 0:
                return {
                    'success': True,
                    'message': f'Chanson supprimée avec succès'
                }
            else:
                return {'success': False, 'message': 'Chanson non trouvée'}
    
    def delete_artist(self, artist_name: str) -> Dict[str, Any]:
        """Supprime un artiste et ses relations"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Artist {name: $artist_name})
            DETACH DELETE a
            RETURN count(a) as deleted_count
            """
            
            result = session.run(query, artist_name=artist_name)
            deleted_count = result.single()['deleted_count']
            
            if deleted_count > 0:
                return {
                    'success': True,
                    'message': f'Artiste "{artist_name}" supprimé avec succès'
                }
            else:
                return {'success': False, 'message': 'Artiste non trouvé'}
    
    # ==================== ANALYTICS OPERATIONS ====================
    
    def get_genre_statistics(self) -> List[Dict[str, Any]]:
        """Statistiques par genre (requête GROUP BY) - Version optimisée mémoire"""
        with self.driver.session() as session:
            query = """
            MATCH (g:Genre)<-[:HAS_GENRE]-(t:Track)
            WITH g.name as genre, t
            RETURN genre,
                   count(t) as track_count,
                   round(avg(t.popularity), 2) as avg_popularity,
                   round(avg(t.energy), 2) as avg_energy,
                   round(avg(t.danceability), 2) as avg_danceability
            ORDER BY track_count DESC
            LIMIT 15
            """
            
            result = session.run(query)
            return [dict(record) for record in result]
    
    def get_artist_statistics(self) -> List[Dict[str, Any]]:
        """Statistiques par artiste - Version optimisée mémoire"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Artist)-[:PERFORMS]->(t:Track)
            WITH a, count(t) as track_count, avg(t.popularity) as avg_popularity
            WHERE track_count >= 2
            RETURN a.name as artist,
                   track_count,
                   round(avg_popularity, 2) as avg_popularity
            ORDER BY track_count DESC
            LIMIT 20
            """
            
            result = session.run(query)
            return [dict(record) for record in result]
    
    def get_popular_songs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les chansons les plus populaires - Version optimisée mémoire"""
        with self.driver.session() as session:
            # Requête optimisée pour éviter les problèmes de mémoire
            query = """
            MATCH (t:Track)
            OPTIONAL MATCH (a:Artist)-[:PERFORMS]->(t)
            OPTIONAL MATCH (t)-[:HAS_GENRE]->(g:Genre)
            
            WITH t, 
                 collect(DISTINCT a.name)[..2] as artists_limited,  // Limiter à 2 artistes
                 g.name as genre
            
            RETURN {
                id: t.id,
                name: t.name,
                popularity: t.popularity,
                energy: t.energy,
                danceability: t.danceability,
                valence: t.valence
            } as track,
            artists_limited as artists,
            genre
            ORDER BY t.popularity DESC
            LIMIT $limit
            """
            
            result = session.run(query, limit=limit)
            
            songs = []
            for record in result:
                track = dict(record['track'])
                track['artists'] = record['artists'] or []
                track['genre'] = record['genre']
                songs.append(track)
            
            return songs
        
    def get_quick_stats(self) -> Dict[str, Any]:
        """Statistiques rapides avec requêtes optimisées pour éviter les problèmes de mémoire"""
        with self.driver.session() as session:
            query = """
            CALL () {
                MATCH (t:Track) RETURN count(t) as total_tracks
            }
            CALL () {
                MATCH (g:Genre) RETURN count(g) as total_genres
            }
            CALL () {
                MATCH (a:Artist) RETURN count(a) as total_artists
            }
            RETURN total_tracks, total_genres, total_artists
            """
            
            result = session.run(query)
            record = result.single()
            if record:
                return {
                    'total_tracks': record['total_tracks'],
                    'total_genres': record['total_genres'],
                    'total_artists': record['total_artists']
                }
            return {}
    
    def get_simple_count(self) -> int:
        """Compte simple des chansons"""
        with self.driver.session() as session:
            query = "MATCH (t:Track) RETURN count(t) as count"
            result = session.run(query)
            record = result.single()
            return record['count'] if record else 0