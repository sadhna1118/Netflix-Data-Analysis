"""
Content-Based Recommendation Engine for Netflix Catalog
Uses TF-IDF Vectorization and Cosine Similarity on content metadata soup
(Genres, Director, Cast, Target Audience, Country, and Description).
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config import PROCESSED_DATA_PATH

class NetflixRecommender:
    """
    Intelligent recommendation engine for streaming content discovery.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else PROCESSED_DATA_PATH
        self.df: Optional[pd.DataFrame] = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.indices = None

    def fit(self, df: Optional[pd.DataFrame] = None):
        """Fit the TF-IDF recommendation engine on content metadata."""
        if df is not None:
            self.df = df.copy()
        elif self.data_path.exists():
            self.df = pd.read_csv(self.data_path)
        else:
            raise ValueError("No data provided and processed CSV not found.")

        # Reset index to ensure alignment
        self.df = self.df.reset_index(drop=True)

        # Create rich metadata soup
        def create_soup(row):
            title = str(row.get('title', ''))
            genres = str(row.get('listed_in', '')).replace(',', ' ')
            director = str(row.get('director', row.get('director_clean', ''))).replace(',', ' ')
            cast = ' '.join(str(row.get('cast', row.get('cast_clean', ''))).split(',')[:4]) # Top 4 cast
            country = str(row.get('country', row.get('country_clean', ''))).replace(',', ' ')
            rating = str(row.get('rating', row.get('rating_clean', '')))
            desc = str(row.get('description', ''))
            audience = str(row.get('target_audience', ''))

            soup = f"{title} {genres} {genres} {director} {cast} {country} {rating} {audience} {desc}"
            return soup.lower()

        self.df['metadata_soup'] = self.df.apply(create_soup, axis=1)

        # Build TF-IDF Matrix with unigrams and bigrams
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=15000,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['metadata_soup'])

        # Create mapping of title to index (case-insensitive)
        self.indices = pd.Series(self.df.index, index=self.df['title'].str.lower()).drop_duplicates()
        print(f"[+] Recommender fitted on {len(self.df)} titles. TF-IDF Shape: {self.tfidf_matrix.shape}")
        return self

    def recommend(self, title: str, top_n: int = 10, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get top N recommended titles for a given movie/show.
        """
        if self.df is None or self.tfidf_matrix is None:
            self.fit()

        title_lower = title.strip().lower()

        # Handle exact match or fuzzy match
        if title_lower not in self.indices:
            matches = self.df[self.df['title'].str.lower().str.contains(title_lower, regex=False, na=False)]
            if matches.empty:
                return []
            idx = matches.index[0]
            matched_title = matches.iloc[0]['title']
        else:
            idx = self.indices[title_lower]
            if isinstance(idx, pd.Series):
                idx = idx.iloc[0]
            matched_title = self.df.iloc[idx]['title']

        # Compute cosine similarity for this title against all titles
        query_vec = self.tfidf_matrix[idx]
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get sorted indices
        sorted_indices = sim_scores.argsort()[::-1]

        results = []
        for i in sorted_indices:
            if i == idx:
                continue # Skip self

            row = self.df.iloc[i]

            if filter_type and str(row.get('type')).lower() != filter_type.lower():
                continue

            score = float(sim_scores[i])
            if score < 0.05:
                break # Low similarity cutoff

            results.append({
                'title': row.get('title'),
                'type': row.get('type'),
                'similarity_score': round(score * 100, 1),
                'genres': row.get('listed_in'),
                'director': row.get('director', row.get('director_clean', 'Unknown')),
                'cast': row.get('cast', row.get('cast_clean', 'Unknown')),
                'country': row.get('country', row.get('country_clean', 'Unknown')),
                'release_year': int(row.get('release_year', 0)),
                'rating': row.get('rating', row.get('rating_clean', 'N/A')),
                'duration': row.get('duration', 'N/A'),
                'description': row.get('description', '')
            })

            if len(results) >= top_n:
                break

        return results

    def get_all_titles(self) -> List[str]:
        """Return list of all available titles sorted alphabetically."""
        if self.df is None:
            self.fit()
        return sorted(self.df['title'].dropna().unique().tolist())
