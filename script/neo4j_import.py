"""
Importer le csv Spotify dans Neo4j en utilisant des batchs pour optimiser les performances.
"""

import pandas as pd
from neo4j import GraphDatabase
import os
from typing import List, Dict
import ast
from dotenv import load_dotenv
import time
from tqdm import tqdm

class SpotifyNeo4jBatchImporter:
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            connection_timeout=30
        )
        self.batch_size = 1000  # Taille des batch
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Efface toutes les données existantes"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Base de données vidée")
    
    def create_constraints_and_indexes(self):
        """Crée les contraintes et index pour optimiser les performances"""
        with self.driver.session() as session:
            # Contraintes d'unicité
            constraints = [
                "CREATE CONSTRAINT track_id_unique IF NOT EXISTS FOR (t:Track) REQUIRE t.track_id IS UNIQUE",
                "CREATE CONSTRAINT artist_name_unique IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE", 
                "CREATE CONSTRAINT album_composite IF NOT EXISTS FOR (al:Album) REQUIRE (al.name, al.artist) IS UNIQUE",
                "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE"
            ]
            
            # Index pour les performances
            indexes = [
                "CREATE INDEX track_popularity IF NOT EXISTS FOR (t:Track) ON (t.popularity)",
                "CREATE INDEX track_genre IF NOT EXISTS FOR (t:Track) ON (t.genre)",
                "CREATE INDEX artist_name IF NOT EXISTS FOR (a:Artist) ON (a.name)"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"Contrainte: {constraint.split()[2]}")
                except Exception as e:
                    print(f"ERREUR :Contrainte {constraint.split()[2]}: {str(e)[:50]}")
            
            for index in indexes:
                try:
                    session.run(index)
                    print(f"Index: {index.split()[2]}")
                except Exception as e:
                    print(f"ERREUR Index {index.split()[2]}: {str(e)[:50]}")

    def parse_artists(self, artists_str: str) -> List[str]:
        """Parse la chaîne d'artistes"""
        if pd.isna(artists_str) or artists_str == "":
            return []
        
        # Essayer de parser comme une liste Python
        try:
            if artists_str.startswith('[') and artists_str.endswith(']'):
                return ast.literal_eval(artists_str)
        except:
            pass
        
        # Séparer par virgules ou points-virgules
        separators = [';', ',', '|']
        for sep in separators:
            if sep in artists_str:
                return [artist.strip().strip("'\"") for artist in artists_str.split(sep)]
        
        return [artists_str.strip()]

    def import_tracks_batch(self, df: pd.DataFrame):
        """Import des tracks par batch"""
        print(f"Import de {len(df)} tracks par batch de {self.batch_size}...")
        
        total_batches = len(range(0, len(df), self.batch_size))
        pbar = tqdm(total=total_batches, desc="Tracks")
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i+self.batch_size]
            retry_count = 0
            max_retries = 3
            batch_success = False
            
            while retry_count < max_retries and not batch_success:
                try:
                    with self.driver.session() as session:
                        tx = session.begin_transaction()
                        
                        for _, row in batch.iterrows():
                            # Gestion sécurisée des valeurs
                            instrumentalness = row['instrumentalness']
                            if isinstance(instrumentalness, str):
                                try:
                                    instrumentalness = float(instrumentalness)
                                except:
                                    instrumentalness = 0.0
                            
                            query = """
                            MERGE (t:Track {track_id: $track_id})
                            SET t.name = $name,
                                t.popularity = $popularity,
                                t.duration_ms = $duration_ms,
                                t.explicit = $explicit,
                                t.danceability = $danceability,
                                t.energy = $energy,
                                t.key = $key,
                                t.loudness = $loudness,
                                t.mode = $mode,
                                t.speechiness = $speechiness,
                                t.acousticness = $acousticness,
                                t.instrumentalness = $instrumentalness,
                                t.liveness = $liveness,
                                t.valence = $valence,
                                t.tempo = $tempo,
                                t.time_signature = $time_signature,
                                t.genre = $genre
                            """
                            
                            tx.run(query,
                                track_id=str(row['track_id']),
                                name=str(row['track_name']),
                                popularity=int(row['popularity']),
                                duration_ms=int(row['duration_ms']),
                                explicit=bool(row['explicit']),
                                danceability=float(row['danceability']),
                                energy=float(row['energy']),
                                key=int(row['key']),
                                loudness=float(row['loudness']),
                                mode=bool(row['mode']),
                                speechiness=float(row['speechiness']),
                                acousticness=float(row['acousticness']),
                                instrumentalness=instrumentalness,
                                liveness=float(row['liveness']),
                                valence=float(row['valence']),
                                tempo=float(row['tempo']),
                                time_signature=int(row['time_signature']),
                                genre=str(row['track_genre'])
                            )
                        
                        tx.commit()
                        batch_success = True
                        pbar.update(1)  # Mettre à jour la barre seulement en cas de succès
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        pbar.set_postfix_str(f"ÉCHEC batch {i//self.batch_size + 1} après {max_retries} tentatives")
                        pbar.update(1)  # Avancer même en cas d'échec final
                        print(f"\nÉchec batch {i//self.batch_size + 1} après {max_retries} tentatives: {e}")
                    else:
                        pbar.set_postfix_str(f"Retry {retry_count}/{max_retries} pour batch {i//self.batch_size + 1}")
                        time.sleep(2)
        
        pbar.close()

    def import_artists_and_relations_batch(self, df: pd.DataFrame):
        """Import des artistes et relations par batch"""
        print(f"Import des artistes et relations par batch...")
        
        total_batches = len(range(0, len(df), self.batch_size))
        pbar = tqdm(total=total_batches, desc="Artists")
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i+self.batch_size]
            
            try:
                with self.driver.session() as session:
                    tx = session.begin_transaction()
                    
                    for _, row in batch.iterrows():
                        artists = self.parse_artists(row['artists'])
                        
                        for artist_name in artists:
                            if artist_name:
                                # Créer l'artiste
                                tx.run("MERGE (a:Artist {name: $name})", name=artist_name)
                                
                                # Créer la relation PERFORMS
                                tx.run("""
                                    MATCH (a:Artist {name: $artist_name})
                                    MATCH (t:Track {track_id: $track_id})
                                    MERGE (a)-[:PERFORMS]->(t)
                                    """, 
                                    artist_name=artist_name, 
                                    track_id=str(row['track_id'])
                                )
                    
                    tx.commit()
                    pbar.update(1)
                    
            except Exception as e:
                pbar.set_postfix_str(f"ERREUR batch {i//self.batch_size + 1}")
                pbar.update(1)
                print(f"\n❌ Erreur batch artistes {i//self.batch_size + 1}: {e}")
        
        pbar.close()

    def import_albums_and_relations_batch(self, df: pd.DataFrame):
        """Import des albums et relations par batch"""
        print(f"Import des albums et relations par batch...")
        
        total_batches = len(range(0, len(df), self.batch_size))
        pbar = tqdm(total=total_batches, desc="Albums")
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i+self.batch_size]
            
            try:
                with self.driver.session() as session:
                    tx = session.begin_transaction()
                    
                    for _, row in batch.iterrows():
                        artists = self.parse_artists(row['artists'])
                        main_artist = artists[0] if artists else "Unknown"
                        
                        # Créer l'album
                        tx.run("""
                            MERGE (al:Album {name: $album_name, artist: $main_artist})
                            """, 
                            album_name=str(row['album_name']), 
                            main_artist=main_artist
                        )
                        
                        # Relations Track -> Album et Artist -> Album
                        tx.run("""
                            MATCH (t:Track {track_id: $track_id})
                            MATCH (al:Album {name: $album_name, artist: $main_artist})
                            MERGE (t)-[:BELONGS_TO]->(al)
                            """, 
                            track_id=str(row['track_id']),
                            album_name=str(row['album_name']),
                            main_artist=main_artist
                        )
                        
                        tx.run("""
                            MATCH (a:Artist {name: $artist_name})
                            MATCH (al:Album {name: $album_name, artist: $main_artist})
                            MERGE (a)-[:CREATED]->(al)
                            """,
                            artist_name=main_artist,
                            album_name=str(row['album_name']),
                            main_artist=main_artist
                        )
                    
                    tx.commit()
                    pbar.update(1)
                    
            except Exception as e:
                pbar.set_postfix_str(f"ERREUR batch {i//self.batch_size + 1}")
                pbar.update(1)
                print(f"\nERREUR batch albums {i//self.batch_size + 1}: {e}")
        
        pbar.close()

    def import_genres_and_relations_batch(self, df: pd.DataFrame):
        """Import des genres et relations par batch"""
        print(f"Import des genres et relations par batch...")
        
        total_batches = len(range(0, len(df), self.batch_size))
        pbar = tqdm(total=total_batches, desc="Genres")
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i+self.batch_size]
            
            try:
                with self.driver.session() as session:
                    tx = session.begin_transaction()
                    
                    for _, row in batch.iterrows():
                        genre_name = str(row['track_genre'])
                        
                        # Créer le genre
                        tx.run("MERGE (g:Genre {name: $name})", name=genre_name)
                        
                        # Relation Track -> Genre
                        tx.run("""
                            MATCH (t:Track {track_id: $track_id})
                            MATCH (g:Genre {name: $genre_name})
                            MERGE (t)-[:HAS_GENRE]->(g)
                            """,
                            track_id=str(row['track_id']),
                            genre_name=genre_name
                        )
                        
                        # Relations Artist -> Genre
                        artists = self.parse_artists(row['artists'])
                        for artist_name in artists:
                            if artist_name:
                                tx.run("""
                                    MATCH (a:Artist {name: $artist_name})
                                    MATCH (g:Genre {name: $genre_name})
                                    MERGE (a)-[:PLAYS_GENRE]->(g)
                                    """,
                                    artist_name=artist_name,
                                    genre_name=genre_name
                                )
                    
                    tx.commit()
                    pbar.update(1)
                    
            except Exception as e:
                pbar.set_postfix_str(f"ERREUR batch {i//self.batch_size + 1}")
                pbar.update(1)
                print(f"\nERREUR batch genres {i//self.batch_size + 1}: {e}")
        
        pbar.close()

    def get_database_stats(self):
        """Affiche les statistiques de la base"""
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
            
            print("\n=== STATISTIQUES DE LA BASE DE DONNÉES ===")
            for name, query in stats_queries:
                try:
                    result = session.run(query).single()
                    count = result['count'] if result else 0
                    print(f"📊 {name}: {count:,}")
                except Exception as e:
                    print(f"❌ Erreur pour {name}: {e}")

def main():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Configuration Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ Erreur: Variables d'environnement manquantes dans le fichier .env")
        return
    
    print("---IMPORT BATCH SPOTIFY DATASET VERS NEO4J---")
    print(f"Connexion: {NEO4J_URI}")
    print(f"Utilisateur: {NEO4J_USER}")
    
    # Chemin vers le dataset
    CSV_PATH = "../data/dataset.csv"
    
    # Initialiser l'importateur
    importer = SpotifyNeo4jBatchImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Charger les données
        print("\nChargement du dataset...")
        df = pd.read_csv(CSV_PATH)
        print(f"Dataset chargé: {len(df):,} lignes")
        
        # Optionnel: vider la base
        # print("\n🧹 Nettoyage de la base...")
        # importer.clear_database()
        
        # Créer les contraintes et index
        print("\n🔧 Création des contraintes et index...")
        importer.create_constraints_and_indexes()
        
        # Import par batch
        print("\nPhase 1: Import des tracks...")
        importer.import_tracks_batch(df)
        
        print("\nPhase 2: Import des artistes et relations...")
        importer.import_artists_and_relations_batch(df)
        
        print("\nPhase 3: Import des albums et relations...")
        importer.import_albums_and_relations_batch(df)
        
        print("\nPhase 4: Import des genres et relations...")
        importer.import_genres_and_relations_batch(df)
        
        # Statistiques finales
        importer.get_database_stats()
        
        print("\nIMPORT TERMINÉ AVEC SUCCÈS !")
        print("\nVotre graphe Neo4j est maintenant prêt pour l'analyse !")
        print("   - Tracks avec métadonnées audio complètes")
        print("   - Relations Artist -[PERFORMS]-> Track")
        print("   - Relations Track -[BELONGS_TO]-> Album") 
        print("   - Relations Track/Artist -[HAS_GENRE/PLAYS_GENRE]-> Genre")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    
    finally:
        importer.close()

if __name__ == "__main__":
    main()