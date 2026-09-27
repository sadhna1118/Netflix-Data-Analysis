"""
Data Pipeline Module for Netflix Data Analysis
Handles loading, cleaning, transforming, feature engineering, and database storage.
"""

import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, List

from src.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, DATABASE_PATH, BASE_DIR

class NetflixDataPipeline:
    """
    Production-grade ETL pipeline for Netflix dataset.
    """

    def __init__(self, raw_path: Path = RAW_DATA_PATH, processed_path: Path = PROCESSED_DATA_PATH, db_path: Path = DATABASE_PATH):
        self.raw_path = Path(raw_path)
        self.processed_path = Path(processed_path)
        self.db_path = Path(db_path)
        
        # Fallback if raw_path doesn't exist yet
        if not self.raw_path.exists():
            alt_path = BASE_DIR / "Netflix-Data-Analysis-main" / "data" / "netflix_titles.csv"
            if alt_path.exists():
                self.raw_path = alt_path

    def load_raw_data(self) -> pd.DataFrame:
        """Load the raw CSV dataset with encoding checks."""
        if not self.raw_path.exists():
            # Check nested folders
            for candidate in [
                BASE_DIR / "data" / "netflix_titles.csv",
                BASE_DIR / "data" / "raw" / "netflix_titles.csv",
                BASE_DIR / "Netflix-Data-Analysis-main" / "data" / "netflix_titles.csv",
                BASE_DIR / "Netflix-Data-Analysis-main" / "netflix_titles.csv"
            ]:
                if candidate.exists():
                    self.raw_path = candidate
                    break

        if not self.raw_path.exists():
            raise FileNotFoundError(f"Raw Netflix data not found at {self.raw_path}")

        print(f"[+] Loading raw dataset from: {self.raw_path}")
        df = pd.read_csv(self.raw_path)
        print(f"[+] Raw dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
        return df

    def clean_and_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data anomalies, handle missing values, and engineer analytical features.
        """
        cleaned = df.copy()

        # 1. Clean string column whitespaces
        str_cols = ['title', 'director', 'cast', 'country', 'rating', 'duration', 'listed_in', 'description']
        for col in str_cols:
            if col in cleaned.columns:
                cleaned[col] = cleaned[col].astype(str).str.strip()
                cleaned[col] = cleaned[col].replace({'nan': np.nan, 'None': np.nan, '': np.nan})

        # 2. Fix known Netflix anomaly: ratings containing duration values (e.g. '74 min', '84 min')
        duration_in_rating = cleaned['rating'].str.contains('min', na=False)
        for idx in cleaned[duration_in_rating].index:
            cleaned.loc[idx, 'duration'] = cleaned.loc[idx, 'rating']
            cleaned.loc[idx, 'rating'] = np.nan

        # 3. Standardize and Impute Missing Values
        cleaned['director_clean'] = cleaned['director'].fillna('Unknown Director')
        cleaned['cast_clean'] = cleaned['cast'].fillna('Unknown Cast')
        cleaned['country_clean'] = cleaned['country'].fillna('Unknown Country')
        cleaned['rating_clean'] = cleaned['rating'].fillna('TV-MA')  # Most common rating mode

        # 4. Date Feature Engineering
        cleaned['date_added_dt'] = pd.to_datetime(cleaned['date_added'].astype(str).str.strip(), errors='coerce')
        
        # Impute missing date_added using release_year + standard release date (Jan 1)
        missing_dates = cleaned['date_added_dt'].isna()
        cleaned.loc[missing_dates, 'date_added_dt'] = pd.to_datetime(
            cleaned.loc[missing_dates, 'release_year'].astype(str) + '-01-01', errors='coerce'
        )

        cleaned['year_added'] = cleaned['date_added_dt'].dt.year.fillna(cleaned['release_year']).astype(int)
        cleaned['month_added'] = cleaned['date_added_dt'].dt.month.fillna(1).astype(int)
        cleaned['month_name_added'] = cleaned['date_added_dt'].dt.month_name().fillna('January')
        cleaned['day_added'] = cleaned['date_added_dt'].dt.day.fillna(1).astype(int)
        cleaned['day_name_added'] = cleaned['date_added_dt'].dt.day_name().fillna('Monday')
        cleaned['quarter_added'] = cleaned['date_added_dt'].dt.quarter.fillna(1).astype(int)

        # 5. Duration Feature Engineering (Parse numeric values)
        def parse_duration(row):
            dur_str = str(row['duration'])
            if pd.isna(dur_str) or dur_str == 'nan':
                return 0, 'Unknown'
            nums = re.findall(r'\d+', dur_str)
            val = int(nums[0]) if nums else 0
            unit = 'min' if 'min' in dur_str.lower() else ('Seasons' if 'season' in dur_str.lower() else 'Unknown')
            return val, unit

        duration_parsed = cleaned.apply(parse_duration, axis=1)
        cleaned['duration_num'] = [d[0] for d in duration_parsed]
        cleaned['duration_type'] = [d[1] for d in duration_parsed]

        # 6. Target Audience Categorization
        audience_map = {
            'TV-Y': 'Kids (0-6)',
            'TV-Y7': 'Older Kids (7+)',
            'TV-Y7-FV': 'Older Kids (7+)',
            'G': 'General Audience',
            'TV-G': 'General Audience',
            'PG': 'Parental Guidance',
            'TV-PG': 'Parental Guidance',
            'PG-13': 'Teens (13+)',
            'TV-14': 'Teens (14+)',
            'R': 'Mature Adults (18+)',
            'TV-MA': 'Mature Adults (18+)',
            'NC-17': 'Adults Only (18+)',
            'NR': 'Not Rated',
            'UR': 'Unrated'
        }
        cleaned['target_audience'] = cleaned['rating_clean'].map(audience_map).fillna('Not Rated')

        # Broad demographic classification
        def classify_demographic(rating):
            if rating in ['TV-Y', 'TV-Y7', 'TV-Y7-FV', 'G', 'TV-G']:
                return 'Kids & Family'
            elif rating in ['PG', 'TV-PG', 'PG-13', 'TV-14']:
                return 'Teens & Young Adults'
            elif rating in ['R', 'TV-MA', 'NC-17']:
                return 'Adults (18+)'
            else:
                return 'Unrated / Other'

        cleaned['age_group'] = cleaned['rating_clean'].apply(classify_demographic)

        # 7. Content Freshness & Acquisition Gap
        cleaned['content_age_at_addition'] = cleaned['year_added'] - cleaned['release_year']
        cleaned['content_age_at_addition'] = cleaned['content_age_at_addition'].apply(lambda x: max(0, x))

        def classify_freshness(gap):
            if gap <= 0:
                return 'Direct-to-Netflix / Same Year'
            elif gap <= 2:
                return 'Recent Release (1-2 yrs)'
            elif gap <= 10:
                return 'Modern Catalog (3-10 yrs)'
            else:
                return 'Classic / Vintage (>10 yrs)'

        cleaned['freshness_category'] = cleaned['content_age_at_addition'].apply(classify_freshness)

        # 8. Primary Country and Primary Genre
        cleaned['primary_country'] = cleaned['country_clean'].apply(lambda x: x.split(',')[0].strip() if x != 'Unknown Country' else 'Unknown')
        cleaned['primary_genre'] = cleaned['listed_in'].apply(lambda x: str(x).split(',')[0].strip() if pd.notna(x) else 'Unknown')

        # 9. Description length
        cleaned['description_length'] = cleaned['description'].astype(str).apply(len)
        cleaned['description_word_count'] = cleaned['description'].astype(str).apply(lambda x: len(x.split()))

        print(f"[+] Transformation complete. Cleaned shape: {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
        return cleaned

    def save_processed(self, df: pd.DataFrame) -> Path:
        """Save cleaned dataset to CSV."""
        self.processed_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.processed_path, index=False)
        print(f"[+] Cleaned dataset saved to: {self.processed_path}")

        # Also copy to root data directory if different
        root_data_csv = BASE_DIR / "data" / "processed" / "netflix_cleaned.csv"
        if root_data_csv != self.processed_path:
            root_data_csv.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(root_data_csv, index=False)

        return self.processed_path

    def create_relational_database(self, df: pd.DataFrame) -> Path:
        """
        Build a high-performance SQLite database with normalized analytical tables:
        - netflix_titles (Main fact table)
        - title_genres (Unnested genres bridge)
        - title_countries (Unnested countries bridge)
        - title_cast (Unnested cast bridge)
        - title_directors (Unnested directors bridge)
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Main Titles Fact Table
        cols_to_save = [
            'show_id', 'type', 'title', 'director_clean', 'cast_clean', 'country_clean',
            'date_added', 'date_added_dt', 'release_year', 'rating_clean', 'duration',
            'duration_num', 'duration_type', 'listed_in', 'description', 'year_added',
            'month_added', 'month_name_added', 'day_name_added', 'quarter_added',
            'target_audience', 'age_group', 'content_age_at_addition',
            'freshness_category', 'primary_country', 'primary_genre'
        ]
        
        main_df = df[[c for c in cols_to_save if c in df.columns]].copy()
        main_df.rename(columns={
            'director_clean': 'director',
            'cast_clean': 'cast',
            'country_clean': 'country',
            'rating_clean': 'rating'
        }, inplace=True)

        main_df.to_sql('netflix_titles', conn, if_exists='replace', index=False)

        # 2. Normalized Genres Table
        genre_records = []
        for _, row in df.iterrows():
            if pd.notna(row.get('listed_in')):
                genres = [g.strip() for g in str(row['listed_in']).split(',') if g.strip()]
                for g in genres:
                    genre_records.append({'show_id': row['show_id'], 'genre': g, 'type': row['type']})
        df_genres = pd.DataFrame(genre_records)
        df_genres.to_sql('title_genres', conn, if_exists='replace', index=False)

        # 3. Normalized Countries Table
        country_records = []
        for _, row in df.iterrows():
            if pd.notna(row.get('country')) and row['country'] != 'Unknown Country':
                countries = [c.strip() for c in str(row['country']).split(',') if c.strip()]
                for c in countries:
                    country_records.append({'show_id': row['show_id'], 'country': c, 'type': row['type']})
        df_countries = pd.DataFrame(country_records)
        df_countries.to_sql('title_countries', conn, if_exists='replace', index=False)

        # 4. Normalized Cast Table
        cast_records = []
        for _, row in df.iterrows():
            if pd.notna(row.get('cast')) and row['cast'] != 'Unknown Cast':
                actors = [a.strip() for a in str(row['cast']).split(',') if a.strip()]
                for a in actors:
                    cast_records.append({'show_id': row['show_id'], 'actor': a, 'type': row['type']})
        df_cast = pd.DataFrame(cast_records)
        df_cast.to_sql('title_cast', conn, if_exists='replace', index=False)

        # 5. Normalized Directors Table
        director_records = []
        for _, row in df.iterrows():
            if pd.notna(row.get('director')) and row['director'] != 'Unknown Director':
                directors = [d.strip() for d in str(row['director']).split(',') if d.strip()]
                for d in directors:
                    director_records.append({'show_id': row['show_id'], 'director': d, 'type': row['type']})
        df_directors = pd.DataFrame(director_records)
        df_directors.to_sql('title_directors', conn, if_exists='replace', index=False)

        # Create Indexes for fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_type ON netflix_titles(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_release_year ON netflix_titles(release_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_rating ON netflix_titles(rating);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genres_genre ON title_genres(genre);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_countries_country ON title_countries(country);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cast_actor ON title_cast(actor);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directors_dir ON title_directors(director);")

        conn.commit()
        conn.close()

        print(f"[+] Relational SQLite database created at: {self.db_path}")
        return self.db_path

    def run(self) -> Tuple[pd.DataFrame, Path, Path]:
        """Execute complete ETL workflow."""
        raw_df = self.load_raw_data()
        cleaned_df = self.clean_and_transform(raw_df)
        csv_path = self.save_processed(cleaned_df)
        db_path = self.create_relational_database(cleaned_df)
        return cleaned_df, csv_path, db_path

if __name__ == "__main__":
    pipeline = NetflixDataPipeline()
    cleaned_df, csv_p, db_p = pipeline.run()
    print("[+] Pipeline execution finished successfully!")
