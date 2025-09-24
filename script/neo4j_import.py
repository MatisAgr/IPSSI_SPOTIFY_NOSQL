"""
Import ULTRA-OPTIMISÉ avec requêtes UNWIND pour Neo4j
Version haute performance pour gros datasets
"""

import pandas as pd
from neo4j import GraphDatabase
import os
from typing import List, Dict
import ast
from dotenv import load_dotenv
import time
from tqdm import tqdm

class SpotifyUltraFastImporter:
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.batch_size = 5000  # Plus gros batch pour UNWIND
    
    def close(self):
        self.driver.close()
    
    def create_constraints_and_indexes(self):
        """Contraintes et index essentiels"""
        with self.driver.session() as session:
            constraints_indexes = [
                "CREATE CONSTRAINT track_id_unique IF NOT EXISTS FOR (t:Track) REQUIRE t.track_id IS UNIQUE",
                "CREATE CONSTRAINT artist_name_unique IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE",
                "CREATE CONSTRAINT album_composite IF NOT EXISTS FOR (al:Album) REQUIRE (al.name, al.artist) IS UNIQUE",
                "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
                "CREATE INDEX track_popularity IF NOT EXISTS FOR (t:Track) ON (t.popularity)"
            ]
            
            for cmd in constraints_indexes:
                try:
                    session.run(cmd)
                    print(f"Validation réussie pour {cmd.split()[2]}")
                except Exception as e:
                    print(f"ERREUR  {cmd.split()[2]}: {e}")

    def parse_artists(self, artists_str: str) -> List[str]:
        """Parse optimisé des artistes"""
        if pd.isna(artists_str) or artists_str == "":
            return []
        
        # Parse rapide
        if ';' in artists_str:
            return [a.strip() for a in artists_str.split(';')]
        if ',' in artists_str:
            return [a.strip() for a in artists_str.split(',')]
        
        return [artists_str.strip()]

    def import_all_data_ultra_fast(self, df: pd.DataFrame):
        """Import par chunks pour éviter les timeouts"""
        chunk_size = 10000  # Plus petit pour éviter timeout
        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        
        print(f"--- Import par chunks de {chunk_size:,} lignes ({total_chunks} chunks)")
        
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(df))
            chunk_df = df.iloc[start_idx:end_idx]
            
            print(f"\n======== Chunk {chunk_idx + 1}/{total_chunks} - Lignes {start_idx:,} à {end_idx:,} ========")
            
            # Préparer les données du chunk
            tracks_data = []
            artists_data = set()
            albums_data = set()
            genres_data = set()
            
            # Relations
            performs_relations = []
            belongs_to_relations = []
            has_genre_relations = []
            plays_genre_relations = []
            created_relations = []
            
            for _, row in tqdm(chunk_df.iterrows(), total=len(chunk_df), desc="Préparation"):
                track_id = str(row['track_id'])
                track_name = str(row['track_name'])
                album_name = str(row['album_name'])
                genre_name = str(row['track_genre'])
                
                # Parse artistes
                artists = self.parse_artists(row['artists'])
                main_artist = artists[0] if artists else "Unknown"
                
                # Données tracks
                instrumentalness = row['instrumentalness']
                if isinstance(instrumentalness, str):
                    try:
                        instrumentalness = float(instrumentalness)
                    except:
                        instrumentalness = 0.0
                
                tracks_data.append({
                    'track_id': track_id,
                    'name': track_name,
                    'popularity': int(row['popularity']),
                    'duration_ms': int(row['duration_ms']),
                    'explicit': bool(row['explicit']),
                    'danceability': float(row['danceability']),
                    'energy': float(row['energy']),
                    'key': int(row['key']),
                    'loudness': float(row['loudness']),
                    'mode': bool(row['mode']),
                    'speechiness': float(row['speechiness']),
                    'acousticness': float(row['acousticness']),
                    'instrumentalness': instrumentalness,
                    'liveness': float(row['liveness']),
                    'valence': float(row['valence']),
                    'tempo': float(row['tempo']),
                    'time_signature': int(row['time_signature']),
                    'genre': genre_name
                })
                
                # Collecte unique des entités
                for artist in artists:
                    if artist:
                        artists_data.add(artist)
                
                albums_data.add((album_name, main_artist))
                genres_data.add(genre_name)
                
                # Relations
                for artist in artists:
                    if artist:
                        performs_relations.append({'artist': artist, 'track_id': track_id})
                        plays_genre_relations.append({'artist': artist, 'genre': genre_name})
                
                belongs_to_relations.append({
                    'track_id': track_id, 
                    'album': album_name, 
                    'artist': main_artist
                })
                
                has_genre_relations.append({'track_id': track_id, 'genre': genre_name})
                created_relations.append({'artist': main_artist, 'album': album_name})
            
            # Import du chunk avec retry
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    with self.driver.session() as session:
                        
                        # 1. Tracks
                        print("- Tracks...")
                        session.run("""
                            UNWIND $tracks as track
                            MERGE (t:Track {track_id: track.track_id})
                            SET t = track
                            """, tracks=tracks_data)
                        
                        # 2. Artists  
                        print("- Artists...")
                        session.run("""
                            UNWIND $artists as artist_name
                            MERGE (a:Artist {name: artist_name})
                            """, artists=list(artists_data))
                        
                        # 3. Albums
                        print("- Albums...")
                        session.run("""
                            UNWIND $albums as album_data
                            MERGE (al:Album {name: album_data.name, artist: album_data.artist})
                            """, albums=[{'name': name, 'artist': artist} for name, artist in albums_data])
                        
                        # 4. Genres
                        print("- Genres...")
                        session.run("""
                            UNWIND $genres as genre_name
                            MERGE (g:Genre {name: genre_name})
                            """, genres=list(genres_data))
                        
                        # 5. Relations (groupées pour éviter timeout)
                        print("- Relations...")
                        session.run("""
                            UNWIND $relations as rel
                            MATCH (a:Artist {name: rel.artist})
                            MATCH (t:Track {track_id: rel.track_id})
                            MERGE (a)-[:PERFORMS]->(t)
                            """, relations=performs_relations)
                        
                        session.run("""
                            UNWIND $relations as rel
                            MATCH (t:Track {track_id: rel.track_id})
                            MATCH (al:Album {name: rel.album, artist: rel.artist})
                            MERGE (t)-[:BELONGS_TO]->(al)
                            """, relations=belongs_to_relations)
                        
                        session.run("""
                            UNWIND $relations as rel
                            MATCH (t:Track {track_id: rel.track_id})
                            MATCH (g:Genre {name: rel.genre})
                            MERGE (t)-[:HAS_GENRE]->(g)
                            """, relations=has_genre_relations)
                        
                        # Relations dédupliquées
                        unique_plays_genre = list({(r['artist'], r['genre']) for r in plays_genre_relations})
                        session.run("""
                            UNWIND $relations as rel
                            MATCH (a:Artist {name: rel.artist})
                            MATCH (g:Genre {name: rel.genre})
                            MERGE (a)-[:PLAYS_GENRE]->(g)
                            """, relations=[{'artist': a, 'genre': g} for a, g in unique_plays_genre])
                        
                        unique_created = list({(r['artist'], r['album']) for r in created_relations})
                        session.run("""
                            UNWIND $relations as rel
                            MATCH (a:Artist {name: rel.artist})
                            MATCH (al:Album {name: rel.album, artist: rel.artist})
                            MERGE (a)-[:CREATED]->(al)
                            """, relations=[{'artist': a, 'album': al} for a, al in unique_created])
                    
                    print(f"Chunk {chunk_idx + 1} terminé")
                    break  # Succès
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Chunk {chunk_idx + 1} échoué après {max_retries} tentatives: {e}")
                        break
                    else:
                        print(f"Retry {retry_count} pour chunk {chunk_idx + 1}")
                        time.sleep(3)

    def get_database_stats(self):
        """Statistiques finales"""
        with self.driver.session() as session:
            stats_queries = [
                ("Tracks", "MATCH (t:Track) RETURN COUNT(t) as count"),
                ("Artists", "MATCH (a:Artist) RETURN COUNT(a) as count"),
                ("Albums", "MATCH (al:Album) RETURN COUNT(al) as count"),
                ("Genres", "MATCH (g:Genre) RETURN COUNT(g) as count"),
                ("Relations PERFORMS", "MATCH ()-[r:PERFORMS]->() RETURN COUNT(r) as count"),
                ("Relations BELONGS_TO", "MATCH ()-[r:BELONGS_TO]->() RETURN COUNT(r) as count"),
                ("Relations CREATED", "MATCH ()-[r:CREATED]->() RETURN COUNT(r) as count"),
                ("Relations HAS_GENRE", "MATCH ()-[r:HAS_GENRE]->() RETURN COUNT(r) as count"),
                ("Relations PLAYS_GENRE", "MATCH ()-[r:PLAYS_GENRE]->() RETURN COUNT(r) as count")
            ]
            
            print("\n=== STATISTIQUES FINALES ===")
            for name, query in stats_queries:
                try:
                    result = session.run(query).single()
                    count = result['count'] if result else 0
                    print(f"6 {name}: {count:,}")
                except Exception as e:
                    print(f"❌ Erreur {name}: {e}")

def main():
    load_dotenv()
    
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ Variables d'environnement manquantes")
        return
    
    print("IMPORT DATA SPOTIFY -> NEO4J")
    print(f"Connexion URI: {NEO4J_URI}")
    
    # notre path de csv
    CSV_PATH = "../data/dataset.csv"
    
    importer = SpotifyUltraFastImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        start_time = time.time()

        print("\n=== Chargement dataset... ===")
        df = pd.read_csv(CSV_PATH)
        print(f"{len(df):,} lignes chargées")
        
        print("\n=== Contraintes et index... ===")
        importer.create_constraints_and_indexes()
        
        print("\n=== IMPORT ULTRA-RAPIDE... ===")
        importer.import_all_data_ultra_fast(df)
        
        importer.get_database_stats()
        
        elapsed = time.time() - start_time
        print(f"\n======== TERMINÉ en {elapsed:.1f} secondes ! ========")
        print(f"Performance: {len(df)/elapsed:.0f} lignes/seconde")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    finally:
        importer.close()

if __name__ == "__main__":
    main()