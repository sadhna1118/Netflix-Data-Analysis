-- ==============================================================================
-- NETFLIX RELATIONAL DATABASE SCHEMA (SQLite / PostgreSQL Compatible)
-- Enterprise schema designed for OLAP Analytics, Business Intelligence & SQL Audits
-- ==============================================================================

-- 1. Main Titles Fact Table
CREATE TABLE IF NOT EXISTS netflix_titles (
    show_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    director TEXT,
    cast TEXT,
    country TEXT,
    date_added TEXT,
    date_added_dt TIMESTAMP,
    release_year INTEGER,
    rating TEXT,
    duration TEXT,
    duration_num INTEGER,
    duration_type TEXT,
    listed_in TEXT,
    description TEXT,
    year_added INTEGER,
    month_added INTEGER,
    month_name_added TEXT,
    day_name_added TEXT,
    quarter_added INTEGER,
    target_audience TEXT,
    age_group TEXT,
    content_age_at_addition INTEGER,
    freshness_category TEXT,
    primary_country TEXT,
    primary_genre TEXT
);

-- 2. Unnested Genres Bridge Table (for 1-to-N genre analytics)
CREATE TABLE IF NOT EXISTS title_genres (
    show_id TEXT,
    genre TEXT,
    type TEXT,
    FOREIGN KEY(show_id) REFERENCES netflix_titles(show_id)
);

-- 3. Unnested Countries Bridge Table (for 1-to-N international production analytics)
CREATE TABLE IF NOT EXISTS title_countries (
    show_id TEXT,
    country TEXT,
    type TEXT,
    FOREIGN KEY(show_id) REFERENCES netflix_titles(show_id)
);

-- 4. Unnested Cast Bridge Table (for talent graph & filmography queries)
CREATE TABLE IF NOT EXISTS title_cast (
    show_id TEXT,
    actor TEXT,
    type TEXT,
    FOREIGN KEY(show_id) REFERENCES netflix_titles(show_id)
);

-- 5. Unnested Directors Bridge Table (for director analytics)
CREATE TABLE IF NOT EXISTS title_directors (
    show_id TEXT,
    director TEXT,
    type TEXT,
    FOREIGN KEY(show_id) REFERENCES netflix_titles(show_id)
);

-- High Performance Indexing
CREATE INDEX IF NOT EXISTS idx_titles_type ON netflix_titles(type);
CREATE INDEX IF NOT EXISTS idx_titles_release_year ON netflix_titles(release_year);
CREATE INDEX IF NOT EXISTS idx_titles_year_added ON netflix_titles(year_added);
CREATE INDEX IF NOT EXISTS idx_titles_rating ON netflix_titles(rating);
CREATE INDEX IF NOT EXISTS idx_genres_genre ON title_genres(genre);
CREATE INDEX IF NOT EXISTS idx_countries_country ON title_countries(country);
CREATE INDEX IF NOT EXISTS idx_cast_actor ON title_cast(actor);
CREATE INDEX IF NOT EXISTS idx_directors_dir ON title_directors(director);
