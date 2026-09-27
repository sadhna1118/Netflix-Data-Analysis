"""
Unit Test Suite for Netflix Data Analytics Pipeline
Validates ETL transformations, data integrity, SQL engine, and recommendation algorithms.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.data_pipeline import NetflixDataPipeline
from src.recommender import NetflixRecommender
from src.db_manager import NetflixDBManager
from src.config import PROCESSED_DATA_PATH, DATABASE_PATH

@pytest.fixture(scope="module")
def pipeline_artifacts():
    """Run data pipeline once for all tests."""
    pipeline = NetflixDataPipeline()
    cleaned_df, csv_path, db_path = pipeline.run()
    return cleaned_df, csv_path, db_path

def test_raw_data_loading(pipeline_artifacts):
    cleaned_df, _, _ = pipeline_artifacts
    assert isinstance(cleaned_df, pd.DataFrame)
    assert len(cleaned_df) > 8000
    assert 'show_id' in cleaned_df.columns
    assert 'title' in cleaned_df.columns

def test_data_cleaning_and_feature_engineering(pipeline_artifacts):
    cleaned_df, _, _ = pipeline_artifacts
    
    # Check engineered columns exist
    required_cols = [
        'director_clean', 'cast_clean', 'country_clean', 'rating_clean',
        'year_added', 'month_added', 'duration_num', 'duration_type',
        'age_group', 'freshness_category'
    ]
    for col in required_cols:
        assert col in cleaned_df.columns, f"Missing engineered column: {col}"

    # Check missing values are properly handled
    assert cleaned_df['director_clean'].isna().sum() == 0
    assert cleaned_df['cast_clean'].isna().sum() == 0
    assert cleaned_df['country_clean'].isna().sum() == 0
    assert cleaned_df['rating_clean'].isna().sum() == 0

def test_duration_parsing(pipeline_artifacts):
    cleaned_df, _, _ = pipeline_artifacts
    movies = cleaned_df[cleaned_df['type'] == 'Movie']
    tv_shows = cleaned_df[cleaned_df['type'] == 'TV Show']

    # Movies should have duration_type 'min' and duration > 0
    valid_movies = movies[movies['duration_num'] > 0]
    assert len(valid_movies) > 0.95 * len(movies)
    assert (valid_movies['duration_type'] == 'min').all()

    # TV Shows should have duration_type 'Seasons'
    valid_tv = tv_shows[tv_shows['duration_num'] > 0]
    assert len(valid_tv) > 0.95 * len(tv_shows)
    assert (valid_tv['duration_type'] == 'Seasons').all()

def test_sqlite_database_tables(pipeline_artifacts):
    _, _, db_path = pipeline_artifacts
    assert Path(db_path).exists()
    
    db_manager = NetflixDBManager(db_path)
    res = db_manager.execute_query("SELECT COUNT(*) AS total FROM netflix_titles;")
    assert res.iloc[0]['total'] > 8000

    # Test normalized tables
    genres_res = db_manager.execute_query("SELECT COUNT(*) AS total FROM title_genres;")
    assert genres_res.iloc[0]['total'] > 8000

    countries_res = db_manager.execute_query("SELECT COUNT(*) AS total FROM title_countries;")
    assert countries_res.iloc[0]['total'] > 5000

def test_recommendation_engine(pipeline_artifacts):
    cleaned_df, _, _ = pipeline_artifacts
    rec = NetflixRecommender()
    rec.fit(cleaned_df)
    
    sample_title = rec.get_all_titles()[0]
    results = rec.recommend(sample_title, top_n=5)
    
    assert len(results) > 0
    assert 'title' in results[0]
    assert 'similarity_score' in results[0]
    assert results[0]['similarity_score'] >= 0
    assert results[0]['title'] != sample_title
