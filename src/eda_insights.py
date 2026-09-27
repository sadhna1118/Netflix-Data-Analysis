"""
Exploratory Data Analysis (EDA) & Visual Insights Engine
Generates publication-quality charts, KPI summaries, and statistical reports.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List

from src.config import (
    PROCESSED_DATA_PATH, FIGURES_DIR, BASE_DIR,
    NETFLIX_RED, NETFLIX_DARK_RED, NETFLIX_BLACK, NETFLIX_DARK_GRAY,
    NETFLIX_LIGHT_GRAY, NETFLIX_ACCENT_BLUE, PALETTE_PRIMARY
)

class NetflixEDAEngine:
    """Analytical engine to extract insights and generate visual reports."""

    def __init__(self, data_path: Path = PROCESSED_DATA_PATH):
        self.data_path = Path(data_path)
        self.df = pd.read_csv(self.data_path) if self.data_path.exists() else None
        
        # Set modern aesthetic matplotlib style
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
        plt.rcParams['axes.edgecolor'] = '#CCCCCC'
        plt.rcParams['axes.linewidth'] = 0.8

    def calculate_kpis(self) -> Dict[str, Any]:
        """Compute top-level business KPIs."""
        if self.df is None:
            return {}

        total_titles = len(self.df)
        movies_df = self.df[self.df['type'] == 'Movie']
        tv_df = self.df[self.df['type'] == 'TV Show']

        total_movies = len(movies_df)
        total_tv = len(tv_df)
        pct_movies = round((total_movies / total_titles) * 100, 1)
        pct_tv = round((total_tv / total_titles) * 100, 1)

        # Country stats
        all_countries = self.df['country_clean'].str.split(',').explode().str.strip()
        all_countries = all_countries[~all_countries.isin(['Unknown Country', ''])]
        top_country = all_countries.mode()[0] if not all_countries.empty else "N/A"
        unique_countries = all_countries.nunique()

        # Genre stats
        all_genres = self.df['listed_in'].str.split(',').explode().str.strip()
        top_genre = all_genres.mode()[0] if not all_genres.empty else "N/A"
        unique_genres = all_genres.nunique()

        # Duration stats
        avg_movie_duration = round(movies_df['duration_num'].mean(), 1)
        max_tv_seasons = tv_df['duration_num'].max()

        # Peak years
        peak_release_year = int(self.df['release_year'].mode()[0])
        peak_added_year = int(self.df['year_added'].mode()[0])

        return {
            'total_titles': total_titles,
            'total_movies': total_movies,
            'total_tv_shows': total_tv,
            'pct_movies': pct_movies,
            'pct_tv': pct_tv,
            'top_country': top_country,
            'unique_countries': unique_countries,
            'top_genre': top_genre,
            'unique_genres': unique_genres,
            'avg_movie_duration_mins': avg_movie_duration,
            'max_tv_seasons': int(max_tv_seasons) if pd.notna(max_tv_seasons) else 0,
            'peak_release_year': peak_release_year,
            'peak_added_year': peak_added_year,
            'mature_content_pct': round((len(self.df[self.df['rating_clean'].isin(['TV-MA', 'R', 'NC-17'])]) / total_titles) * 100, 1)
        }

    def generate_all_charts(self, output_dir: Path = FIGURES_DIR) -> List[Path]:
        """Generate all 10 high-resolution charts."""
        output_dir.mkdir(parents=True, exist_ok=True)
        img_legacy_dir = BASE_DIR / "images"
        img_legacy_dir.mkdir(parents=True, exist_ok=True)
        img_subfolder_dir = BASE_DIR / "Netflix-Data-Analysis-main" / "images"
        img_subfolder_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        def save_fig(fig, filename):
            p1 = output_dir / filename
            fig.savefig(p1, dpi=300, bbox_inches='tight')
            # Also save to images/ for markdown references
            p2 = img_legacy_dir / filename
            fig.savefig(p2, dpi=300, bbox_inches='tight')
            p3 = img_subfolder_dir / filename
            fig.savefig(p3, dpi=300, bbox_inches='tight')
            plt.close(fig)
            generated_files.append(p1)
            print(f"[+] Saved figure: {filename}")

        # 1. Movies vs TV Shows (Content Distribution)
        fig, ax = plt.subplots(figsize=(8, 6))
        type_counts = self.df['type'].value_counts()
        colors = [NETFLIX_RED, NETFLIX_DARK_GRAY]
        wedges, texts, autotexts = ax.pie(
            type_counts,
            labels=type_counts.index,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors,
            explode=(0.05, 0),
            textprops={'fontsize': 12, 'weight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        for autotext in autotexts:
            autotext.set_color('white')
        ax.set_title('Netflix Content Library: Movies vs TV Shows', fontsize=14, weight='bold', pad=20)
        save_fig(fig, 'movies_vs_tvshows.png')

        # 2. Top 10 Content Producing Countries
        fig, ax = plt.subplots(figsize=(10, 6))
        countries_series = self.df['country_clean'].str.split(',').explode().str.strip()
        top_countries = countries_series[~countries_series.isin(['Unknown Country', ''])].value_counts().head(10)
        y_pos = range(len(top_countries))
        bars = ax.barh(y_pos, top_countries.values, color=NETFLIX_RED, edgecolor='none', height=0.65)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_countries.index, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Total Titles Produced / Co-Produced', fontsize=11, weight='bold')
        ax.set_title('Top 10 Global Content Producing Countries on Netflix', fontsize=14, weight='bold', pad=15)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 25, bar.get_y() + bar.get_height()/2, f'{int(width):,}', va='center', fontsize=10, weight='bold', color='#333333')
        ax.set_xlim(0, max(top_countries.values) * 1.15)
        save_fig(fig, 'top_countries.png')

        # 3. Top 10 Genres
        fig, ax = plt.subplots(figsize=(10, 6))
        genres_series = self.df['listed_in'].str.split(',').explode().str.strip()
        top_genres = genres_series.value_counts().head(10)
        bars = ax.barh(range(len(top_genres)), top_genres.values, color='#221F1F', edgecolor='none', height=0.65)
        ax.set_yticks(range(len(top_genres)))
        ax.set_yticklabels(top_genres.index, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Number of Titles', fontsize=11, weight='bold')
        ax.set_title('Top 10 Most Prevalent Genres on Netflix', fontsize=14, weight='bold', pad=15)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 20, bar.get_y() + bar.get_height()/2, f'{int(width):,}', va='center', fontsize=10, weight='bold', color=NETFLIX_RED)
        ax.set_xlim(0, max(top_genres.values) * 1.15)
        save_fig(fig, 'top_genres.png')

        # 4. Release Year Trend vs Year Added
        fig, ax = plt.subplots(figsize=(12, 6))
        yearly_added = self.df[self.df['year_added'] >= 2008].groupby(['year_added', 'type']).size().unstack(fill_value=0)
        ax.plot(yearly_added.index, yearly_added['Movie'], marker='o', linewidth=2.5, color=NETFLIX_RED, label='Movies Added')
        ax.plot(yearly_added.index, yearly_added['TV Show'], marker='s', linewidth=2.5, color=NETFLIX_ACCENT_BLUE, label='TV Shows Added')
        ax.set_title('Netflix Catalog Expansion Trajectory by Addition Year (2008 - 2021)', fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Year Added to Netflix', fontsize=11, weight='bold')
        ax.set_ylabel('Annual Titles Added', fontsize=11, weight='bold')
        ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=11)
        save_fig(fig, 'release_trend.png')

        # 5. Rating Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        rating_counts = self.df['rating_clean'].value_counts()
        colors = [NETFLIX_RED if r in ['TV-MA', 'R'] else '#555555' for r in rating_counts.index]
        bars = ax.bar(rating_counts.index, rating_counts.values, color=colors, edgecolor='white', linewidth=1)
        ax.set_title('Content Ratings Distribution (Adult TV-MA Dominance in Red)', fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Content Rating Tier', fontsize=11, weight='bold')
        ax.set_ylabel('Total Titles', fontsize=11, weight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 25, f'{int(height)}', ha='center', fontsize=9, weight='bold')
        ax.set_ylim(0, max(rating_counts.values) * 1.12)
        save_fig(fig, 'ratings.png')

        # 6. Duration Analysis (Movies)
        fig, ax = plt.subplots(figsize=(10, 6))
        movie_durations = self.df[(self.df['type'] == 'Movie') & (self.df['duration_num'] > 0)]['duration_num']
        ax.hist(movie_durations, bins=35, color=NETFLIX_RED, alpha=0.8, edgecolor='white', density=False)
        ax.axvline(movie_durations.median(), color=NETFLIX_BLACK, linestyle='--', linewidth=2, label=f'Median: {int(movie_durations.median())} mins')
        ax.axvline(movie_durations.mean(), color=NETFLIX_ACCENT_BLUE, linestyle=':', linewidth=2, label=f'Mean: {movie_durations.mean():.1f} mins')
        ax.set_title('Distribution of Movie Runtimes (Peak: 90 - 110 Minutes)', fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Duration (Minutes)', fontsize=11, weight='bold')
        ax.set_ylabel('Frequency', fontsize=11, weight='bold')
        ax.legend(fontsize=11)
        save_fig(fig, 'duration.png')

        # 7. Top Directors
        fig, ax = plt.subplots(figsize=(10, 6))
        directors = self.df['director_clean'].str.split(',').explode().str.strip()
        top_directors = directors[~directors.isin(['Unknown Director', ''])].value_counts().head(10)
        bars = ax.barh(range(len(top_directors)), top_directors.values, color=NETFLIX_RED, height=0.65)
        ax.set_yticks(range(len(top_directors)))
        ax.set_yticklabels(top_directors.index, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Directed Titles on Netflix', fontsize=11, weight='bold')
        ax.set_title('Top 10 Most Prolific Directors on Netflix', fontsize=14, weight='bold', pad=15)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center', fontsize=10, weight='bold')
        ax.set_xlim(0, max(top_directors.values) + 3)
        save_fig(fig, 'top_directors.png')

        # 8. Top Actors
        fig, ax = plt.subplots(figsize=(10, 6))
        actors = self.df['cast_clean'].str.split(',').explode().str.strip()
        top_actors = actors[~actors.isin(['Unknown Cast', ''])].value_counts().head(10)
        bars = ax.barh(range(len(top_actors)), top_actors.values, color='#221F1F', height=0.65)
        ax.set_yticks(range(len(top_actors)))
        ax.set_yticklabels(top_actors.index, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('Appearances in Netflix Titles', fontsize=11, weight='bold')
        ax.set_title('Top 10 Most Featured Actors on Netflix', fontsize=14, weight='bold', pad=15)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center', fontsize=10, weight='bold', color=NETFLIX_RED)
        ax.set_xlim(0, max(top_actors.values) + 4)
        save_fig(fig, 'top_actors.png')

        # 9. Monthly Content Addition Seasonality
        fig, ax = plt.subplots(figsize=(10, 6))
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        monthly_df = self.df['month_name_added'].value_counts().reindex(month_order).fillna(0)
        bars = ax.bar(monthly_df.index, monthly_df.values, color=NETFLIX_RED, edgecolor='white')
        ax.set_title('Seasonal Content Addition Patterns by Month (Peaks in July & Dec)', fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Month Added', fontsize=11, weight='bold')
        ax.set_ylabel('Total Titles Added', fontsize=11, weight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 10, f'{int(height)}', ha='center', fontsize=9, weight='bold')
        ax.set_ylim(0, max(monthly_df.values) * 1.12)
        save_fig(fig, 'monthly_content.png')

        # 10. Content Age vs Catalog Licensing
        fig, ax = plt.subplots(figsize=(10, 6))
        freshness_counts = self.df['freshness_category'].value_counts()
        colors = [NETFLIX_RED, '#E57373', '#757575', '#221F1F']
        bars = ax.bar(freshness_counts.index, freshness_counts.values, color=colors[:len(freshness_counts)], edgecolor='white')
        ax.set_title('Content Strategy: Direct-to-Netflix vs Catalog Licensing Gap', fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Content Freshness Category (Year Added - Release Year)', fontsize=11, weight='bold')
        ax.set_ylabel('Titles Count', fontsize=11, weight='bold')
        plt.xticks(rotation=15, ha='right', fontsize=10)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 20, f'{int(height)} ({height/len(self.df)*100:.1f}%)', ha='center', fontsize=9, weight='bold')
        ax.set_ylim(0, max(freshness_counts.values) * 1.15)
        save_fig(fig, 'freshness_acquisition.png')

        return generated_files
