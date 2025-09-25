# 🎵 IPSSI Spotify NoSQL Project

Projet d'analyse de données musicales Spotify utilisant Neo4j comme base de données graphe et Streamlit pour l'interface web interactive avec fonctionnalités CRUD complètes.

## 📋 Table des matières
- [Architecture du projet](#architecture-du-projet)
- [Configuration requise](#configuration-requise)
- [Installation et configuration](#installation-et-configuration)
- [Lancement des scripts](#lancement-des-scripts)
- [Structure des données Neo4j](#structure-des-données-neo4j)
- [Fonctionnalités de l'application](#fonctionnalités-de-lapplication)
- [Analyses et requêtes](#analyses-et-requêtes)
- [Gestion de projet](#gestion-de-projet)
- [Présentation des résultats](#présentation-des-résultats)

## 🏗️ Architecture du projet

```mermaid
graph TB
    subgraph "Données"
        CSV[📄 dataset.csv]
        Env[🔐 .env<br/>Credentials Neo4j]
    end
    
    subgraph "Scripts d'import et analyse"
        Test[🔍 test_connection.py<br/>Test Neo4j Aura]
        Import[⚡ neo4j_import.py<br/>Import ultra-optimisé<br/>Batch UNWIND]
        Queries[📊 cypher_queries.py<br/>Requêtes d'analyse]
    end
    
    subgraph "Base de données Neo4j Aura"
        Neo4j[(🗄️ Neo4j Graph DB<br/>Nodes & Relations)]
    end
    
    subgraph "Application Streamlit Web"
        Main[🏠 main.py<br/>Dashboard principal]
        Backend[⚙️ backend.py<br/>CRUD Operations]
        
        subgraph "Pages Web"
            Analytics[📊 analytics.py<br/>Statistiques & Graphiques]
            Search[🔍 search_song.py<br/>Recherche multicritères]
            Edit[✏️ edit_song.py<br/>Modification chansons]
            Upload[➕ upload_song.py<br/>Ajout nouvelles chansons]
        end
    end
    
    subgraph "Analyse avancée"
        Notebook[📓 analyse_spotify_neo4j.ipynb<br/>Jupyter Analysis]
    end
    
    CSV --> Import
    Env --> Import
    Env --> Backend
    Test --> Neo4j
    Import --> Neo4j
    Neo4j --> Backend
    Neo4j --> Queries
    Neo4j --> Notebook
    Backend --> Main
    Backend --> Analytics
    Backend --> Search
    Backend --> Edit
    Backend --> Upload
    
    classDef dataClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef scriptClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dbClass fill:#fff3e0,stroke:#e65100,stroke-width:3px
    classDef webClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef analysisClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class CSV,Env dataClass
    class Test,Import,Queries scriptClass
    class Neo4j dbClass
    class Main,Backend,Analytics,Search,Edit,Upload webClass
    class Notebook analysisClass
```

## ⚙️ Configuration requise

### Technologies utilisées
- **Python 3.8+** avec packages: `neo4j`, `pandas`, `streamlit`, `plotly`, `python-dotenv`, `numpy`, `tqdm`
- **Neo4j Aura** (base de données cloud) avec credentials dans fichier `.env`
- **Navigateur web moderne** pour l'interface Streamlit

### Dataset
- **~114,000 chansons** avec 19 caractéristiques audio (danceability, energy, valence, etc.)
- **Genres**: acoustic, afrobeat, alt-rock, ambient, etc.
- **Métadonnées**: popularité, durée, tempo, key, etc.

## 🚀 Installation et configuration

1. **Cloner le repository**
   ```powershell
   git clone https://github.com/MatisAgr/IPSSI_SPOTIFY_NOSQL.git
   cd IPSSI_SPOTIFY_NOSQL
   ```

2. **Créer environnement virtuel Python**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configuration Neo4j Aura** - Créer `.env` à la racine :
   ```env
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password-here
   NEO4J_DATABASE=neo4j
   AURA_INSTANCEID=instanceid
   AURA_INSTANCENAME=instancename
   ```

## 🛠️ Lancement des scripts

1. **Test de connexion Neo4j Aura**
   ```powershell
   cd script
   python test_connection.py
   ```
   > Vérifie la connexion et affiche les statistiques actuelles de la DB

2. **Import ultra-optimisé du dataset**
   ```powershell
   cd script
   python neo4j_import.py
   ```
   > Import par batch de 10k avec requêtes UNWIND pour performance maximale

3. **Lancer l'application web Streamlit**
   ```powershell
   cd streamlit
   streamlit run main.py
   ```
   > Interface web complète sur `http://localhost:8501`

4. **Exécuter les analyses Cypher**
   ```powershell
   cd script
   python cypher_queries.py
   ```
   > Requêtes d'analyse: top artistes, genres populaires, corrélations

5. **Analyse Jupyter (optionnel)**
   ```powershell
   jupyter notebook analyse_spotify_neo4j.ipynb
   ```

## 📊 Structure des données Neo4j

### Modèle de graphe optimisé

```mermaid
erDiagram
    TRACK {
        string track_id PK "ID unique Spotify"
        string name "Nom de la chanson"
        int popularity "0-100"
        int duration_ms "Durée en millisecondes"
        boolean explicit "Contenu explicite"
        float danceability "0.0-1.0"
        float energy "0.0-1.0"
        float valence "0.0-1.0"
        float acousticness "0.0-1.0"
        float instrumentalness "0.0-1.0"
        float liveness "0.0-1.0"
        float loudness "dB"
        float speechiness "0.0-1.0"
        float tempo "BPM"
        int time_signature "1-7"
        int mode "0=Minor, 1=Major"
        int key "0-11"
    }
    
    ARTIST {
        string name PK "Nom de l'artiste"
        float avg_popularity "Popularité moyenne calculée"
    }
    
    ALBUM {
        string name "Nom de l'album"
        string artist "Artiste principal"
        int track_count "Nombre de tracks"
    }
    
    GENRE {
        string name PK "acoustic, rock, pop, etc."
        int track_count "Nombre de tracks"
        float avg_popularity "Popularité moyenne"
    }
    
    ARTIST ||--o{ TRACK : "PERFORMS"
    TRACK ||--|| ALBUM : "BELONGS_TO"
    TRACK ||--|| GENRE : "HAS_GENRE"
    ARTIST ||--o{ GENRE : "PLAYS_GENRE"
    ARTIST ||--o{ ALBUM : "CREATED"
```

### Contraintes et index Neo4j

```cypher
-- Contraintes d'unicité
CREATE CONSTRAINT track_id_unique FOR (t:Track) REQUIRE t.track_id IS UNIQUE;
CREATE CONSTRAINT artist_name_unique FOR (a:Artist) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT genre_name_unique FOR (g:Genre) REQUIRE g.name IS UNIQUE;
CREATE CONSTRAINT album_composite FOR (al:Album) REQUIRE (al.name, al.artist) IS UNIQUE;

-- Index pour les performances
CREATE INDEX track_popularity FOR (t:Track) ON (t.popularity);
```

## 🌐 Fonctionnalités de l'application Streamlit

### Interface utilisateur complète

```mermaid
mindmap
    root((🎵 Spotify Neo4j App))
        🏠 Dashboard Principal
            ✅ Test connexion Neo4j
            📊 Statistiques rapides
            🔗 Navigation vers pages
            📋 Aperçu données récentes
        🔍 Recherche Avancée
            🔎 Recherche générale
            🎭 Filtrage par genre
            👤 Recherche par artiste
            ⭐ Chansons populaires
            📑 Pagination
        ➕ Gestion Chansons
            ➕ Ajout nouvelle chanson
            🎵 Formulaire complet
            ✏️ Modification existante
            🗑️ Suppression
        📊 Analytics Interactifs
            📈 Vue d'ensemble metrics
            🎭 Statistiques par genre
            👤 Statistiques par artiste
            ⭐ Analyse popularité
            🎵 Caractéristiques audio
            🔗 Corrélations
```

### Fonctionnalités CRUD détaillées

#### 🏠 **Dashboard Principal** (`main.py`)
- **Connexion automatique** à Neo4j Aura avec cache
- **Statistiques rapides** en sidebar (genres, artistes)
- **Navigation intuitive** vers toutes les fonctionnalités
- **Aperçu temps réel** des chansons populaires

#### 🔍 **Recherche Multicritères** (`search_song.py`)
- **Recherche textuelle** globale (chansons, artistes, albums)
- **Filtrage par genre** avec dropdown dynamique
- **Recherche par artiste** spécifique
- **Top chansons populaires** avec limite configurable
- **Pagination** pour grandes listes
- **Statistiques contextuelles** par genre

#### ➕ **Gestion des Chansons** (`upload_song.py`)
- **Ajout complet** avec toutes les métadonnées
- **Validation des données** (popularité 0-100, tempo, etc.)
- **Parsing intelligent** des artistes multiples
- **Relations automatiques** (Album, Genre, Artiste)
- **Génération d'ID unique** si nécessaire

#### ✏️ **Modification** (`edit_song.py`)
- **Sélection depuis recherche** ou ID direct
- **Formulaire pré-rempli** avec données actuelles
- **Mise à jour sélective** des propriétés
- **Préservation des relations** complexes
- **Actions supplémentaires** (voir stats, supprimer)

#### 📊 **Analytics Avancés** (`analytics.py`)
- **Vue d'ensemble** avec métriques clés
- **Graphiques interactifs** Plotly (pie charts, histogrammes)
- **Analyses par genre** avec GROUP BY Cypher
- **Statistiques artistes** (polyvalence, popularité)
- **Corrélations audio** entre caractéristiques
- **Visualisations temps réel** des données

### Backend robuste (`backend.py`)

#### 🔧 **Opérations CRUD complètes**
- **CREATE**: `create_song()`, `create_artist()`, `create_album()`
- **READ**: `search_songs()`, `get_song_by_id()`, `get_songs_by_genre()`
- **UPDATE**: `update_song()`, `update_artist()` 
- **DELETE**: `delete_song()`, `delete_artist()`

#### 📊 **Analytics intégrés**
- `get_genre_statistics()` - Statistiques par genre
- `get_artist_statistics()` - Analyses par artiste  
- `get_popular_songs()` - Top chansons
- Gestion automatique des **relations complexes**

## Analyses et requêtes Cypher

### Exemples de requêtes Cypher utilisées

#### 1. **Top 10 Artistes les plus populaires**
```cypher
MATCH (a:Artist)-[:PERFORMS]->(t:Track)
RETURN a.name as artist, 
       COUNT(t) as nb_tracks, 
       AVG(t.popularity) as avg_popularity,
       MAX(t.popularity) as max_popularity
ORDER BY avg_popularity DESC
LIMIT 10
```

#### 2. **Analyse des genres musicaux**
```cypher
MATCH (g:Genre)<-[:HAS_GENRE]-(t:Track)
RETURN g.name as genre, 
       COUNT(t) as nb_tracks, 
       AVG(t.popularity) as avg_popularity,
       AVG(t.energy) as avg_energy,
       AVG(t.danceability) as avg_danceability
ORDER BY avg_popularity DESC
```

#### 3. **Albums avec le plus de tracks**
```cypher
MATCH (al:Album)<-[:BELONGS_TO]-(t:Track)
RETURN al.name as album, 
       al.artist as main_artist,
       COUNT(t) as nb_tracks,
       AVG(t.popularity) as avg_popularity
ORDER BY nb_tracks DESC
LIMIT 20
```

#### 4. **Artistes polyvalents (multi-genres)**
```cypher
MATCH (a:Artist)-[:PLAYS_GENRE]->(g:Genre)
RETURN a.name as artist,
       COLLECT(DISTINCT g.name) as genres,
       SIZE(COLLECT(DISTINCT g.name)) as nb_genres
ORDER BY nb_genres DESC
LIMIT 15
```

### Performance et optimisation

- **Import ultra-rapide** : Batch UNWIND de 10k lignes
- **Contraintes d'unicité** pour éviter les doublons
- **Index sur popularité** pour les recherches fréquentes
- **Relations optimisées** pour navigation rapide dans le graphe
- **Cache Streamlit** pour performances web

## 📋 Gestion de projet

### Lien Trello - Suivi des tâches

**Tableau Trello - IPSSI Spotify NoSQL**

```mermaid
kanban
    À faire
        🚀 Optimisation requêtes complexes
        📖 Documentation API complète
        🎨 Amélioration UI/UX
    
    En cours  
        📊 Dashboard analytics avancés
        🔍 Filtres de recherche étendus
        📱 README
        ⚡ Cache optimisé
    
    Terminé
        ✅ Configuration Neo4j Aura
        ✅ Import dataset ultra-rapide
        ✅ Backend CRUD complet
        ✅ Interface Streamlit
        ✅ Pages de recherche/modification
        ✅ Analytics de base
        ✅ Documentation README
```

### Répartition des tâches équipe

| 👤 Membre | 🎯 Responsabilités |
|-----------|-------------------|
| **Matis** | Configuration Neo4j Aura, Scripts d'import optimisés |
| **Julien** | Interface Streamlit, Pages CRUD, UI/UX, Documentation |
| **Carl** | Backend, Requêtes Cypher, Analytics, Notebook Jupyter |

## 🎯 Présentation des résultats


#### 📊 Statistiques du dataset analysé

```mermaid
pie title Distribution des genres principaux dans le dataset
    "Indie Pop" : 1000
    "Industrial : 1000
    "Electronic" : 1000
    "Emo" : 1000
    "Accoustic" : 1000
    "Garage" : 1000
    "Disco" : 1000
    "Country" : 1000
    "British" : 1000
    "Funk" : 1000
```

#### 🎵 Caractéristiques audio moyennes par genre

```mermaid
xychart-beta
    title "Énergie vs Danceability par genre"
    x-axis ["Pop", "Rock", "Electronic", "Hip-Hop", "Jazz", "Classical"]
    y-axis "Score (0-1)" 0 --> 1
    line [0.7, 0.8, 0.75, 0.65, 0.4, 0.3]
    line [0.65, 0.5, 0.8, 0.75, 0.45, 0.25]
```

#### 🏆 Indicateurs de performance technique

| 🔧 Métrique | 📈 Valeur | 💡 Description |
|-------------|-----------|----------------|
| **Chansons importées** | ~114,000 | Dataset Spotify complet |
| **Performance import** | 2,500 lignes/sec | Import ultra-optimisé UNWIND |
| **Nœuds Neo4j** | ~180,000 | Tracks + Artists + Albums + Genres |
| **Relations créées** | ~350,000 | PERFORMS, BELONGS_TO, HAS_GENRE, etc. |
| **Pages Streamlit** | 5 | Dashboard, Search, CRUD, Analytics |
| **Requêtes Cypher** | 15+ | Analyses statistiques avancées |

### Architecture technique validée

```mermaid
graph LR
    A[📊 Dataset CSV<br/>114k chansons] --> B[⚡ Import Neo4j<br/>Ultra-rapide]
    B --> C[🗄️ Graph Database<br/>Neo4j Aura]
    C --> D[🌐 Interface Web<br/>Streamlit]
    C --> E[📈 Analytics<br/>Cypher Queries]
    
    D --> F[🔍 Recherche<br/>Multi-critères]
    D --> G[✏️ CRUD<br/>Complet]
    D --> H[📊 Visualisations<br/>Interactives]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#e8f5e8
    style D fill:#f3e5f5
    style E fill:#fce4ec
    style F fill:#e1f5fe
    style G fill:#fff8e1
    style H fill:#f1f8e9
```

### Fonctionnalités démontrées

✅ **Import massif performant** avec contraintes et index  
✅ **Interface CRUD complète** pour gestion des données  
✅ **Recherche multicritères** avancée  
✅ **Analytics temps réel** avec visualisations  
✅ **Relations graphe complexes** optimisées  
✅ **Architecture scalable** Neo4j + Streamlit  

### Technologies validées

- **Neo4j Aura** : Base de données graphe cloud haute performance
- **Python Streamlit** : Interface web interactive rapide  
- **Requêtes Cypher** : Analyse de graphe native et puissante
- **Plotly** : Visualisations interactives professionnelles
- **Architecture modulaire** : Séparation backend/frontend claire

---

## 📝 Notes techniques importantes

⚠️ **Prérequis essentiels :**
- Connexion Neo4j Aura configurée dans `.env`
- Python 3.8+ avec packages requirements.txt
- Dataset CSV disponible dans `/data/dataset.csv`

🔧 **Configuration recommandée :**
- L'application Streamlit sera accessible sur `http://localhost:8501`
- L'import peut prendre 3-5 minutes selon la connexion
- Cache Streamlit activé pour performances optimales

🚀 **Déploiement possible sur :**
- Streamlit Cloud (gratuit)
- Heroku avec Neo4j Aura
- Docker containerisé

---

*📚 Projet réalisé dans le cadre du cours NoSQL - IPSSI 2025  
🎯 Démonstration d'architecture Neo4j + Streamlit pour analytics musicaux*