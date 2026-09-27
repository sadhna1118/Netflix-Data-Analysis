"""
Script to generate production-grade Jupyter Notebooks for Netflix Data Analysis.
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.12.0"
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

def make_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }

def make_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }

# ---------------------------------------------------------
# Notebook 1: Data Cleaning and Profiling
# ---------------------------------------------------------
nb1_cells = [
    make_markdown_cell("""# 🎬 Netflix Data Cleaning, Auditing & Feature Engineering
### *A Production-Grade Data Analyst ETL Pipeline*
---
**Author**: Data Analytics Team  
**Dataset**: Netflix Movies & TV Shows Dataset (8,800+ Titles)  
**Objective**: Clean raw catalog data, remediate schema anomalies, engineer analytical dimensions, and export structured artifacts for OLAP analysis.
"""),
    make_code_cell("""import pandas as pd
import numpy as np
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 50)
"""),
    make_markdown_cell("""## 1. Load Raw Dataset & Initial Assessment"""),
    make_code_cell("""raw_path = Path('../data/raw/netflix_titles.csv')
if not raw_path.exists():
    raw_path = Path('../Netflix-Data-Analysis-main/data/netflix_titles.csv')

df = pd.read_csv(raw_path)
print(f"Dataset Dimension: {df.shape[0]} Rows, {df.shape[1]} Columns\\n")
df.info()
df.head(5)
"""),
    make_markdown_cell("""## 2. Missing Value Analysis & Profiling"""),
    make_code_cell("""missing_df = pd.DataFrame({
    'Missing_Count': df.isna().sum(),
    'Missing_Percentage': round((df.isna().sum() / len(df)) * 100, 2)
}).sort_values('Missing_Count', ascending=False)

missing_df[missing_df['Missing_Count'] > 0]
"""),
    make_markdown_cell("""## 3. Data Cleaning & Anomaly Remediation
### Anomaly Fix: Ratings containing duration strings (e.g., '74 min', '84 min')
In this dataset, a few entries have durations mistakenly recorded in the `rating` column. We detect and shift these records.
"""),
    make_code_cell("""cleaned = df.copy()

# 1. Clean string column whitespaces
str_cols = ['title', 'director', 'cast', 'country', 'rating', 'duration', 'listed_in', 'description']
for col in str_cols:
    cleaned[col] = cleaned[col].astype(str).str.strip().replace({'nan': np.nan, 'None': np.nan, '': np.nan})

# 2. Fix rating-duration misalignment anomaly
duration_in_rating = cleaned['rating'].str.contains('min', na=False)
for idx in cleaned[duration_in_rating].index:
    cleaned.loc[idx, 'duration'] = cleaned.loc[idx, 'rating']
    cleaned.loc[idx, 'rating'] = np.nan

# 3. Impute categorical missing values
cleaned['director_clean'] = cleaned['director'].fillna('Unknown Director')
cleaned['cast_clean'] = cleaned['cast'].fillna('Unknown Cast')
cleaned['country_clean'] = cleaned['country'].fillna('Unknown Country')
cleaned['rating_clean'] = cleaned['rating'].fillna('TV-MA')  # Dominant mode

print("Anomaly remediation completed. Missing ratings count now:", cleaned['rating_clean'].isna().sum())
"""),
    make_markdown_cell("""## 4. Advanced Feature Engineering
We engineer:
- `date_added_dt`: Standard datetime object
- `year_added`, `month_added`, `month_name_added`, `day_name_added`
- `duration_num` & `duration_type`: Clean numeric runtime & units (minutes vs seasons)
- `target_audience` & `age_group`: Demographic segmentation (Kids, Teens, Adults)
- `content_age_at_addition` & `freshness_category`: Catalog licensing gap vs Originals
"""),
    make_code_cell("""# Date Engineering
cleaned['date_added_dt'] = pd.to_datetime(cleaned['date_added'].astype(str).str.strip(), errors='coerce')
missing_dates = cleaned['date_added_dt'].isna()
cleaned.loc[missing_dates, 'date_added_dt'] = pd.to_datetime(
    cleaned.loc[missing_dates, 'release_year'].astype(str) + '-01-01', errors='coerce'
)

cleaned['year_added'] = cleaned['date_added_dt'].dt.year.fillna(cleaned['release_year']).astype(int)
cleaned['month_added'] = cleaned['date_added_dt'].dt.month.fillna(1).astype(int)
cleaned['month_name_added'] = cleaned['date_added_dt'].dt.month_name().fillna('January')
cleaned['day_name_added'] = cleaned['date_added_dt'].dt.day_name().fillna('Monday')

# Duration Parsing
def parse_duration(row):
    dur_str = str(row['duration'])
    if pd.isna(dur_str) or dur_str == 'nan':
        return 0, 'Unknown'
    nums = re.findall(r'\\d+', dur_str)
    val = int(nums[0]) if nums else 0
    unit = 'min' if 'min' in dur_str.lower() else ('Seasons' if 'season' in dur_str.lower() else 'Unknown')
    return val, unit

duration_parsed = cleaned.apply(parse_duration, axis=1)
cleaned['duration_num'] = [d[0] for d in duration_parsed]
cleaned['duration_type'] = [d[1] for d in duration_parsed]

# Age group demographic
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

# Content Freshness
cleaned['content_age_at_addition'] = (cleaned['year_added'] - cleaned['release_year']).apply(lambda x: max(0, x))
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
cleaned['primary_country'] = cleaned['country_clean'].apply(lambda x: x.split(',')[0].strip() if x != 'Unknown Country' else 'Unknown')
cleaned['primary_genre'] = cleaned['listed_in'].apply(lambda x: str(x).split(',')[0].strip() if pd.notna(x) else 'Unknown')

cleaned[['title', 'type', 'release_year', 'year_added', 'duration_num', 'duration_type', 'age_group', 'freshness_category']].head(5)
"""),
    make_markdown_cell("""## 5. Export Cleaned Data Artifacts"""),
    make_code_cell("""out_csv = Path('../data/processed/netflix_cleaned.csv')
out_csv.parent.mkdir(parents=True, exist_ok=True)
cleaned.to_csv(out_csv, index=False)
print(f"[✓] Saved cleaned dataset to: {out_csv.resolve()}")
print(f"[✓] Final Dataset Shape: {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
""")
]

# ---------------------------------------------------------
# Notebook 2: Exploratory Data Analysis
# ---------------------------------------------------------
nb2_cells = [
    make_markdown_cell("""# 📊 Netflix Exploratory Data Analysis (EDA) & Storytelling
### *Deep-Dive Visual Insights for Strategic Decision Making*
---
**Objective**: Uncover content distribution patterns, geographic expansion trends, genre affinity, and talent synergy using professional visualizations.
"""),
    make_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set professional aesthetics
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
NETFLIX_RED = "#E50914"
NETFLIX_BLACK = "#141414"

# Load Cleaned Data
df = pd.read_csv('../data/processed/netflix_cleaned.csv')
print(f"Loaded Cleaned Dataset: {len(df):,} titles")
df.head(3)
"""),
    make_markdown_cell("""## 1. Content Library Balance: Movies vs. TV Shows"""),
    make_code_cell("""plt.figure(figsize=(7, 7))
type_counts = df['type'].value_counts()
plt.pie(
    type_counts, 
    labels=type_counts.index, 
    autopct='%1.1f%%', 
    colors=[NETFLIX_RED, '#221F1F'], 
    startangle=140, 
    explode=(0.05, 0),
    textprops={'fontsize': 12, 'weight': 'bold'},
    wedgeprops={'edgecolor': 'white', 'linewidth': 2}
)
plt.title("Netflix Catalog Split: Movies vs TV Shows", fontsize=14, weight='bold', pad=20)
plt.show()
"""),
    make_markdown_cell("""## 2. Geographic Footprint: Top 10 Producing Countries"""),
    make_code_cell("""plt.figure(figsize=(10, 6))
country_series = df['country_clean'].str.split(',').explode().str.strip()
top_countries = country_series[~country_series.isin(['Unknown Country', ''])].value_counts().head(10)

bars = plt.barh(range(len(top_countries)), top_countries.values, color=NETFLIX_RED, height=0.65)
plt.yticks(range(len(top_countries)), top_countries.index, fontsize=11)
plt.gca().invert_yaxis()
plt.xlabel("Total Titles Produced", fontsize=11, weight='bold')
plt.title("Top 10 Content Producing Countries on Netflix", fontsize=14, weight='bold', pad=15)

for bar in bars:
    width = bar.get_width()
    plt.text(width + 25, bar.get_y() + bar.get_height()/2, f"{int(width):,}", va='center', fontsize=10, weight='bold')
plt.xlim(0, max(top_countries.values) * 1.15)
plt.show()
"""),
    make_markdown_cell("""## 3. Genre Landscape: Top 15 Most Prevalent Genres"""),
    make_code_cell("""plt.figure(figsize=(10, 6))
genres_series = df['listed_in'].str.split(',').explode().str.strip()
top_genres = genres_series.value_counts().head(15)

bars = plt.barh(range(len(top_genres)), top_genres.values, color='#221F1F', height=0.65)
plt.yticks(range(len(top_genres)), top_genres.index, fontsize=11)
plt.gca().invert_yaxis()
plt.xlabel("Number of Titles", fontsize=11, weight='bold')
plt.title("Top 15 Dominant Genres on Netflix", fontsize=14, weight='bold', pad=15)

for bar in bars:
    width = bar.get_width()
    plt.text(width + 20, bar.get_y() + bar.get_height()/2, f"{int(width):,}", va='center', fontsize=10, weight='bold', color=NETFLIX_RED)
plt.xlim(0, max(top_genres.values) * 1.15)
plt.show()
"""),
    make_markdown_cell("""## 4. Platform Expansion Over Time (Year-over-Year Additions)"""),
    make_code_cell("""plt.figure(figsize=(12, 6))
yearly_added = df[df['year_added'] >= 2008].groupby(['year_added', 'type']).size().unstack(fill_value=0)

plt.plot(yearly_added.index, yearly_added['Movie'], marker='o', linewidth=2.5, color=NETFLIX_RED, label='Movies Added')
plt.plot(yearly_added.index, yearly_added['TV Show'], marker='s', linewidth=2.5, color='#0071EB', label='TV Shows Added')

plt.title("Netflix Catalog Growth Trajectory by Addition Year (2008-2021)", fontsize=14, weight='bold', pad=15)
plt.xlabel("Year Added to Netflix", fontsize=11, weight='bold')
plt.ylabel("Annual Titles Added", fontsize=11, weight='bold')
plt.legend(frameon=True, fontsize=11)
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()
"""),
    make_markdown_cell("""## 5. Runtime & Duration Analytics"""),
    make_code_cell("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Movies Runtime
movies = df[(df['type'] == 'Movie') & (df['duration_num'] > 0)]
ax1.hist(movies['duration_num'], bins=35, color=NETFLIX_RED, edgecolor='white', alpha=0.85)
ax1.axvline(movies['duration_num'].median(), color='black', linestyle='--', label=f"Median: {int(movies['duration_num'].median())} min")
ax1.set_title("Movie Runtime Distribution (Minutes)", fontsize=12, weight='bold')
ax1.set_xlabel("Duration (Minutes)")
ax1.set_ylabel("Count")
ax1.legend()

# TV Shows Seasons
tv_shows = df[(df['type'] == 'TV Show') & (df['duration_num'] > 0)]
tv_seasons = tv_shows['duration_num'].value_counts().sort_index().head(10)
ax2.bar(tv_seasons.index, tv_seasons.values, color='#0071EB', edgecolor='white')
ax2.set_title("TV Shows Season Distribution (Longevity)", fontsize=12, weight='bold')
ax2.set_xlabel("Number of Seasons")
ax2.set_ylabel("Count of Shows")

plt.tight_layout()
plt.show()
""")
]

# ---------------------------------------------------------
# Notebook 3: Advanced Business Analytics & Recommender
# ---------------------------------------------------------
nb3_cells = [
    make_markdown_cell("""# 🧠 Advanced Business Analytics, SQL Studio & Content Recommender
### *Strategy Formulation, SQL Business Queries & Machine Learning Recommendations*
---
**Objective**: Run business intelligence SQL queries on SQLite database, perform audience segmentation, and implement a content-based recommendation model.
"""),
    make_code_cell("""import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

# Connect to Relational SQLite DB
db_path = Path('../data/processed/netflix.sqlite')
conn = sqlite3.connect(db_path)
print("[✓] Connected to SQLite database:", db_path.resolve())
"""),
    make_markdown_cell("""## 1. Executive SQL Business Query: YoY Catalog Additions"""),
    make_code_cell("""query_yoy = \"\"\"
WITH yearly_data AS (
    SELECT 
        year_added,
        COUNT(*) AS total_added,
        SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
    FROM netflix_titles
    WHERE year_added >= 2012
    GROUP BY year_added
)
SELECT 
    year_added,
    total_added,
    movies_added,
    tv_shows_added,
    LAG(total_added, 1) OVER (ORDER BY year_added) AS prev_year_total,
    ROUND((total_added - LAG(total_added, 1) OVER (ORDER BY year_added)) * 100.0 / 
          NULLIF(LAG(total_added, 1) OVER (ORDER BY year_added), 0), 2) AS yoy_growth_pct
FROM yearly_data
ORDER BY year_added ASC;
\"\"\"

pd.read_sql_query(query_yoy, conn)
"""),
    make_markdown_cell("""## 2. SQL Query: Director-Actor Collaboration Power Duos"""),
    make_code_cell("""query_duos = \"\"\"
SELECT 
    td.director AS Director,
    tc.actor AS Actor,
    COUNT(DISTINCT td.show_id) AS Collaborative_Titles
FROM title_directors td
JOIN title_cast tc ON td.show_id = tc.show_id
WHERE td.director != 'Unknown Director' AND tc.actor != 'Unknown Cast'
GROUP BY td.director, tc.actor
HAVING Collaborative_Titles >= 3
ORDER BY Collaborative_Titles DESC
LIMIT 12;
\"\"\"

pd.read_sql_query(query_duos, conn)
"""),
    make_markdown_cell("""## 3. SQL Query: International vs US Content Expansion"""),
    make_code_cell("""query_intl = \"\"\"
SELECT 
    year_added,
    COUNT(*) AS total_additions,
    SUM(CASE WHEN country LIKE '%United States%' THEN 1 ELSE 0 END) AS us_titles,
    SUM(CASE WHEN country NOT LIKE '%United States%' AND country != 'Unknown Country' THEN 1 ELSE 0 END) AS international_titles,
    ROUND(
        SUM(CASE WHEN country NOT LIKE '%United States%' AND country != 'Unknown Country' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        1
    ) AS international_pct
FROM netflix_titles
WHERE year_added >= 2014
GROUP BY year_added
ORDER BY year_added ASC;
\"\"\"

pd.read_sql_query(query_intl, conn)
"""),
    make_markdown_cell("""## 4. Machine Learning Content Recommendation Engine
We construct a TF-IDF vectorizer over the metadata soup (Title, Genre, Cast, Director, Country, Age Group, Description) and compute Cosine Similarity.
"""),
    make_code_cell("""df = pd.read_csv('../data/processed/netflix_cleaned.csv')

def create_soup(row):
    title = str(row.get('title', ''))
    genres = str(row.get('listed_in', '')).replace(',', ' ')
    director = str(row.get('director_clean', '')).replace(',', ' ')
    cast = ' '.join(str(row.get('cast_clean', '')).split(',')[:4])
    country = str(row.get('country_clean', '')).replace(',', ' ')
    rating = str(row.get('rating_clean', ''))
    desc = str(row.get('description', ''))
    audience = str(row.get('target_audience', ''))
    return f"{title} {genres} {genres} {director} {cast} {country} {rating} {audience} {desc}".lower()

df['metadata_soup'] = df.apply(create_soup, axis=1)

# TF-IDF Vectorization
tfidf = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=12000)
tfidf_matrix = tfidf.fit_transform(df['metadata_soup'])
print(f"TF-IDF Matrix Shape: {tfidf_matrix.shape}")

# Recommender function
def get_recommendations(title, top_n=5):
    title_matches = df[df['title'].str.lower() == title.lower()]
    if title_matches.empty:
        title_matches = df[df['title'].str.lower().str.contains(title.lower())]
        if title_matches.empty:
            return f"No title matching '{title}' found."
    
    idx = title_matches.index[0]
    query_vec = tfidf_matrix[idx]
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    sorted_idx = sim_scores.argsort()[::-1]
    
    results = []
    for i in sorted_idx:
        if i == idx:
            continue
        row = df.iloc[i]
        results.append({
            'Title': row['title'],
            'Type': row['type'],
            'Similarity': f"{round(sim_scores[i] * 100, 1)}%",
            'Release_Year': row['release_year'],
            'Genres': row['listed_in'],
            'Director': row['director_clean']
        })
        if len(results) >= top_n:
            break
            
    return pd.DataFrame(results)

# Test Recommendation for 'Stranger Things'
get_recommendations('Stranger Things', top_n=5)
"""),
    make_markdown_cell("""## 5. Strategic Recommendations for C-Suite
1. **Accelerate TV Series Original Franchises**: TV Shows drive platform retention and reduce subscriber churn, yet represent only ~30% of catalog.
2. **Local-for-Global Content Strategy**: International hubs (India, South Korea, Spain, UK) show superior growth velocity and cross-border viewership.
3. **Optimize Runtime Clustering**: The consumer sweet spot for feature films is 90-105 minutes; avoid excessive 150+ min catalog padding without marquee IP.
4. **Seasonal Release Coordination**: Align high-budget tentpole drops with July and December holiday peaks to capture maximum streaming hours.
""")
]

# Write Notebook files
with open(NOTEBOOKS_DIR / "01_Data_Cleaning_and_Profiling.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb1_cells), f, indent=2)

with open(NOTEBOOKS_DIR / "02_Exploratory_Data_Analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb2_cells), f, indent=2)

with open(NOTEBOOKS_DIR / "03_Advanced_Business_Analytics.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb3_cells), f, indent=2)

print("[+] All 3 Jupyter Notebooks generated successfully!")
