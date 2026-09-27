"""
Database Manager and SQL Analytics Studio for Netflix Dataset
Provides SQLite connectivity, automated table queries, and real-world business analyst query templates.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config import DATABASE_PATH

# Pre-defined real-world Business Intelligence Queries
BUSINESS_QUERIES: Dict[str, Dict[str, str]] = {
    "1. Content Type Breakdown": {
        "description": "Calculate total volume and market percentage split between Movies and TV Shows.",
        "sql": """
        SELECT 
            type AS Content_Type,
            COUNT(*) AS Total_Titles,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS Percentage_Share
        FROM netflix_titles
        GROUP BY type;
        """
    },
    "2. Top 10 Content Producing Countries": {
        "description": "Identify global content hubs with distinct movie vs TV show counts.",
        "sql": """
        SELECT 
            country,
            COUNT(*) AS Total_Titles,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows,
            ROUND(SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS TV_Show_Pct
        FROM title_countries
        WHERE country != 'Unknown Country' AND country != ''
        GROUP BY country
        ORDER BY Total_Titles DESC
        LIMIT 10;
        """
    },
    "3. Top 15 Most In-Demand Genres": {
        "description": "Rank most frequent genres across the entire Netflix streaming catalog.",
        "sql": """
        SELECT 
            genre,
            COUNT(*) AS Total_Titles,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies_Count,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows_Count
        FROM title_genres
        GROUP BY genre
        ORDER BY Total_Titles DESC
        LIMIT 15;
        """
    },
    "4. Year-over-Year (YoY) Catalog Additions": {
        "description": "Analyze Netflix platform scaling trajectory by year content was added.",
        "sql": """
        SELECT 
            year_added AS Year_Added,
            COUNT(*) AS Titles_Added,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies_Added,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows_Added,
            ROUND((COUNT(*) - LAG(COUNT(*), 1) OVER (ORDER BY year_added)) * 100.0 / 
                  NULLIF(LAG(COUNT(*), 1) OVER (ORDER BY year_added), 0), 2) AS YoY_Growth_Pct
        FROM netflix_titles
        WHERE year_added >= 2008
        GROUP BY year_added
        ORDER BY year_added ASC;
        """
    },
    "5. Content Freshness & Acquisition Strategy": {
        "description": "Distribution of content freshness (Direct-to-Netflix vs Catalog Licensing).",
        "sql": """
        SELECT 
            freshness_category AS Freshness_Tier,
            COUNT(*) AS Titles_Count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS Catalog_Pct,
            ROUND(AVG(release_year), 0) AS Avg_Release_Year
        FROM netflix_titles
        GROUP BY freshness_category
        ORDER BY Titles_Count DESC;
        """
    },
    "6. Most Prolific Directors": {
        "description": "Top 10 directors by title count and their primary country.",
        "sql": """
        SELECT 
            td.director AS Director_Name,
            COUNT(DISTINCT nt.show_id) AS Total_Works,
            GROUP_CONCAT(DISTINCT nt.type) AS Content_Types,
            GROUP_CONCAT(DISTINCT nt.primary_genre) AS Primary_Genres
        FROM title_directors td
        JOIN netflix_titles nt ON td.show_id = nt.show_id
        WHERE td.director != 'Unknown Director'
        GROUP BY td.director
        ORDER BY Total_Works DESC
        LIMIT 10;
        """
    },
    "7. Top 15 Most Cast Actors": {
        "description": "Actors appearing most frequently across Netflix originals and licensed titles.",
        "sql": """
        SELECT 
            tc.actor AS Actor_Name,
            COUNT(DISTINCT nt.show_id) AS Titles_Count,
            SUM(CASE WHEN nt.type = 'Movie' THEN 1 ELSE 0 END) AS Movies,
            SUM(CASE WHEN nt.type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows,
            GROUP_CONCAT(DISTINCT nt.primary_country) AS Dominant_Countries
        FROM title_cast tc
        JOIN netflix_titles nt ON tc.show_id = nt.show_id
        WHERE tc.actor != 'Unknown Cast'
        GROUP BY tc.actor
        ORDER BY Titles_Count DESC
        LIMIT 15;
        """
    },
    "8. Audience Rating Demographics": {
        "description": "Breakdown of mature (18+) vs family/teen content proportions.",
        "sql": """
        SELECT 
            age_group AS Audience_Segment,
            COUNT(*) AS Total_Titles,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS Percentage_Share,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows
        FROM netflix_titles
        GROUP BY age_group
        ORDER BY Total_Titles DESC;
        """
    },
    "9. Release Seasonality (Monthly Addition Trends)": {
        "description": "Analyze which calendar months see peak content drops.",
        "sql": """
        SELECT 
            month_added AS Month_Num,
            month_name_added AS Month_Name,
            COUNT(*) AS Total_Releases,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows
        FROM netflix_titles
        GROUP BY month_added, month_name_added
        ORDER BY month_added ASC;
        """
    },
    "10. TV Shows with Highest Longevity (Seasons)": {
        "description": "TV Series that achieved the longest runtime on the platform.",
        "sql": """
        SELECT 
            title AS Show_Title,
            country AS Country,
            release_year AS Release_Year,
            duration_num AS Total_Seasons,
            rating AS Rating,
            listed_in AS Genres
        FROM netflix_titles
        WHERE type = 'TV Show'
        ORDER BY duration_num DESC
        LIMIT 10;
        """
    },
    "11. Movie Runtime Distribution Quintiles": {
        "description": "Distribution buckets for Movie duration in minutes.",
        "sql": """
        SELECT 
            CASE 
                WHEN duration_num < 60 THEN '1. Short Film (<60 min)'
                WHEN duration_num BETWEEN 60 AND 90 THEN '2. Feature Lite (60-90 min)'
                WHEN duration_num BETWEEN 91 AND 120 THEN '3. Standard Feature (91-120 min)'
                WHEN duration_num BETWEEN 121 AND 150 THEN '4. Extended Feature (121-150 min)'
                ELSE '5. Epic (>150 min)'
            END AS Duration_Bucket,
            COUNT(*) AS Movie_Count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'Movie'), 2) AS Pct_Of_Movies,
            ROUND(AVG(duration_num), 1) AS Avg_Minutes
        FROM netflix_titles
        WHERE type = 'Movie' AND duration_num > 0
        GROUP BY Duration_Bucket
        ORDER BY Duration_Bucket ASC;
        """
    },
    "12. Director & Actor Power Duos": {
        "description": "Frequent director-actor collaborations on Netflix (3+ shared projects).",
        "sql": """
        SELECT 
            td.director AS Director,
            tc.actor AS Actor,
            COUNT(DISTINCT td.show_id) AS Collaborative_Works
        FROM title_directors td
        JOIN title_cast tc ON td.show_id = tc.show_id
        WHERE td.director != 'Unknown Director' AND tc.actor != 'Unknown Cast'
        GROUP BY td.director, tc.actor
        HAVING Collaborative_Works >= 3
        ORDER BY Collaborative_Works DESC
        LIMIT 15;
        """
    },
    "13. Multi-Country Co-Productions": {
        "description": "Cross-border collaborative titles produced by 2 or more countries.",
        "sql": """
        SELECT 
            show_id,
            title,
            type,
            release_year,
            country_clean AS Production_Countries,
            num_countries
        FROM netflix_titles
        WHERE num_countries > 1
        ORDER BY num_countries DESC, release_year DESC
        LIMIT 15;
        """
    },
    "14. Direct-to-Platform Speed (Added in Release Year)": {
        "description": "Fresh content added in the exact same year it was theatrically/broadcast released.",
        "sql": """
        SELECT 
            release_year AS Release_Year,
            COUNT(*) AS Same_Year_Additions,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE year_added = release_year), 2) AS Share_Of_Fresh_Additions
        FROM netflix_titles
        WHERE year_added = release_year AND release_year >= 2015
        GROUP BY release_year
        ORDER BY release_year DESC;
        """
    },
    "15. Vintage Classics in Catalog (Pre-1980)": {
        "description": "Oldest historic films and series preserved in Netflix's global library.",
        "sql": """
        SELECT 
            title,
            type,
            release_year,
            country_clean AS Country,
            rating,
            duration,
            listed_in AS Genres
        FROM netflix_titles
        WHERE release_year < 1980
        ORDER BY release_year ASC
        LIMIT 15;
        """
    },
    "16. Genre Distribution Across Content Types": {
        "description": "Comprehensive matrix of genres split across Movies vs TV Shows.",
        "sql": """
        SELECT 
            genre AS Genre_Name,
            COUNT(*) AS Total_Titles,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS Movies_Count,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS TV_Shows_Count,
            ROUND(AVG(release_year), 0) AS Avg_Release_Year
        FROM title_genres
        GROUP BY genre
        ORDER BY Total_Titles DESC
        LIMIT 20;
        """
    }
}

class NetflixDBManager:
    """Manages SQLite connections and executes SQL queries."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH

    def get_connection(self) -> sqlite3.Connection:
        """Get an open SQLite connection."""
        return sqlite3.connect(self.db_path)

    def execute_query(self, sql_query: str) -> pd.DataFrame:
        """Execute any custom SQL query and return a pandas DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query(sql_query, conn)

    def get_preset_queries(self) -> Dict[str, Dict[str, str]]:
        """Return library of business intelligence SQL queries."""
        return BUSINESS_QUERIES

    def get_tables_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return table schemas and columns."""
        info = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                cols = cursor.fetchall()
                info[table] = [{'cid': c[0], 'name': c[1], 'type': c[2], 'notnull': c[3]} for c in cols]
        return info

