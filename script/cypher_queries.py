"""
tester les requete cypher
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import pandas as pd

class SpotifyAnalyzer:
    
    def __init__(self):
        # Charger les variables d'environnement
        load_dotenv()
        
        # Configuration Neo4j
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USERNAME') 
        self.password = os.getenv('NEO4J_PASSWORD')
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError("Variables d'environnement Neo4j manquantes dans le fichier .env")
            
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def execute_query(self, query, description):
        """Exécute une requête et retourne les résultats"""
        print(f"\n=== {description} ===")
        with self.driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]
            if records:
                df = pd.DataFrame(records)
                print(df.to_string(index=False))
                return df
            else:
                print("Aucun résultat trouvé")
                return None

    
    def top_artists(self):
        """1. Top 10 des artistes les plus populaires"""
        query = """
        MATCH (a:Artist)-[:PERFORMS]->(t:Track)
        RETURN a.name as artist, 
               COUNT(t) as nb_tracks, 
               AVG(t.popularity) as avg_popularity,
               MAX(t.popularity) as max_popularity
        ORDER BY avg_popularity DESC
        LIMIT 10
        """
        return self.execute_query(query, "Top 10 des artistes les plus populaires")
    
    def popular_genres(self):
        """2. Genres les plus populaires"""
        query = """
        MATCH (g:Genre)<-[:HAS_GENRE]-(t:Track)
        RETURN g.name as genre, 
               COUNT(t) as nb_tracks, 
               AVG(t.popularity) as avg_popularity,
               AVG(t.energy) as avg_energy,
               AVG(t.danceability) as avg_danceability
        ORDER BY avg_popularity DESC
        """
        return self.execute_query(query, "Genres les plus populaires")
    
    def biggest_albums(self):
        """3. Albums avec le plus de tracks"""
        query = """
        MATCH (al:Album)<-[:BELONGS_TO]-(t:Track)
        RETURN al.name as album, 
               al.artist as main_artist,
               COUNT(t) as nb_tracks,
               AVG(t.popularity) as avg_popularity
        ORDER BY nb_tracks DESC
        LIMIT 20
        """
        return self.execute_query(query, "Albums avec le plus de tracks")
    
    def versatile_artists(self):
        """4. Artistes les plus polyvalents (qui jouent le plus de genres différents)"""
        query = """
        MATCH (a:Artist)-[:PLAYS_GENRE]->(g:Genre)
        RETURN a.name as artist,
               COLLECT(DISTINCT g.name) as genres,
               SIZE(COLLECT(DISTINCT g.name)) as nb_genres
        ORDER BY nb_genres DESC
        LIMIT 15
        """
        return self.execute_query(query, "Artistes les plus polyvalents")
    
    def popularity_analysis(self):
        """5. Corrélations entre caractéristiques musicales et popularité"""
        query = """
        MATCH (t:Track)
        WHERE t.popularity > 70
        WITH AVG(t.danceability) as high_pop_danceability,
             AVG(t.energy) as high_pop_energy,
             AVG(t.valence) as high_pop_valence,
             AVG(t.tempo) as high_pop_tempo,
             COUNT(t) as high_pop_count
        MATCH (t:Track)
        WHERE t.popularity < 30
        RETURN high_pop_danceability, high_pop_energy, high_pop_valence, high_pop_tempo, high_pop_count,
               AVG(t.danceability) as low_pop_danceability,
               AVG(t.energy) as low_pop_energy,
               AVG(t.valence) as low_pop_valence,
               AVG(t.tempo) as low_pop_tempo,
               COUNT(t) as low_pop_count
        """
        return self.execute_query(query, "Analyse popularité vs caractéristiques musicales")
    
    def collaborations(self):
        """6. Collaborations (artistes qui ont travaillé ensemble)"""
        query = """
        MATCH (a1:Artist)-[:PERFORMS]->(t:Track)<-[:PERFORMS]-(a2:Artist)
        WHERE a1.name < a2.name
        RETURN a1.name as artist1, 
               a2.name as artist2, 
               COUNT(t) as collaborations,
               COLLECT(t.name)[0..5] as sample_tracks
        ORDER BY collaborations DESC
        LIMIT 20
        """
        return self.execute_query(query, "Collaborations entre artistes")
    
    def run_all_analyses(self):
        """Exécute toutes les analyses"""
        print("🎵 ANALYSE COMPLÈTE DES DONNÉES SPOTIFY 🎵")
        
        analyses = [
            self.top_artists,
            self.popular_genres,
            self.biggest_albums,
            self.versatile_artists,
            self.popularity_analysis,
            self.collaborations
        ]
        
        results = {}
        for analysis in analyses:
            try:
                result = analysis()
                results[analysis.__doc__] = result
            except Exception as e:
                print(f"Erreur lors de l'analyse {analysis.__doc__}: {e}")
        
        return results

def main():
    analyzer = SpotifyAnalyzer()
    
    try:
        # Lancer toutes les analyses
        analyzer.run_all_analyses()
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()