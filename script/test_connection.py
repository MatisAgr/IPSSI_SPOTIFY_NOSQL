"""
Script de test de connexion Neo4j AuraDB - Version simplifiée
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

def test_connection():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les paramètres depuis le .env
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Erreur: Variables d'environnement manquantes dans le fichier .env")
        return False
    
    print("=== TEST CONNEXION NEO4J AURADB ===")
    print(f"URI: {NEO4J_URI}")
    print(f"User: {NEO4J_USER}")
    print("Password: [MASQUÉ]")
    
    try:
        # Test de connexion
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            result = session.run("RETURN 'Connexion OK!' as message")
            message = result.single()["message"]
            print(f"{message}")
            
            # Stats actuelles
            nodes = session.run("MATCH (n) RETURN COUNT(n) as count").single()['count']
            rels = session.run("MATCH ()-[r]->() RETURN COUNT(r) as count").single()['count']
            
            print(f"Noeuds: {nodes}")
            print(f"Relations: {rels}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    if test_connection():
        print("\nVous pouvez maintenant lancer neo4j_import.py !")
    else:
        print("\nVérifiez votre mot de passe dans la console Neo4j AuraDB")