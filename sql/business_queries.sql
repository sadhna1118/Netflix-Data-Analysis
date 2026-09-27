-- ==============================================================================
-- 15 REAL-WORLD DATA ANALYST BUSINESS INTELLIGENCE SQL QUERIES FOR NETFLIX
-- Used for Portfolio Demonstrations, Technical Interviews, and Strategy Analysis
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Q1: Content Mix Proportion: Movies vs. TV Shows
-- Business Context: Understand the core catalog balance between short-form engagement (Movies)
-- and high-retention episodic content (TV Series).
-- ------------------------------------------------------------------------------
SELECT 
    type AS content_type,
    COUNT(*) AS total_titles,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS percentage_share
FROM netflix_titles
GROUP BY type;


-- ------------------------------------------------------------------------------
-- Q2: Top 10 Content Producing Countries with Format Specialization
-- Business Context: Identify key international hubs and determine if they lean towards Movies or TV Series.
-- ------------------------------------------------------------------------------
SELECT 
    country,
    COUNT(*) AS total_titles,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_count,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_count,
    ROUND(SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS tv_show_pct
FROM title_countries
WHERE country != 'Unknown Country' AND country != ''
GROUP BY country
ORDER BY total_titles DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- Q3: Year-over-Year (YoY) Catalog Additions & Expansion Velocity
-- Business Context: Track annual addition trends and calculate growth rate percentages.
-- ------------------------------------------------------------------------------
WITH yearly_data AS (
    SELECT 
        year_added,
        COUNT(*) AS total_added,
        SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
    FROM netflix_titles
    WHERE year_added >= 2010
    GROUP BY year_added
)
SELECT 
    year_added,
    total_added,
    movies_added,
    tv_shows_added,
    LAG(total_added, 1) OVER (ORDER BY year_added) AS previous_year_added,
    ROUND(
        (total_added - LAG(total_added, 1) OVER (ORDER BY year_added)) * 100.0 / 
        NULLIF(LAG(total_added, 1) OVER (ORDER BY year_added), 0), 
        2
    ) AS yoy_growth_percentage
FROM yearly_data
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- Q4: Top 15 Most Dominant Content Categories / Genres
-- Business Context: Determine the highest density genres to guide original productions.
-- ------------------------------------------------------------------------------
SELECT 
    genre,
    COUNT(*) AS total_titles,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM title_genres
GROUP BY genre
ORDER BY total_titles DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Q5: Content Freshness vs. Catalog Licensing Strategy
-- Business Context: Calculate how many years elapse between theatrical release and Netflix addition.
-- ------------------------------------------------------------------------------
SELECT 
    freshness_category,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct_of_library,
    ROUND(AVG(content_age_at_addition), 1) AS avg_licensing_lag_years
FROM netflix_titles
GROUP BY freshness_category
ORDER BY title_count DESC;


-- ------------------------------------------------------------------------------
-- Q6: Top 10 Most Prolific Directors by Title Volume
-- Business Context: Identify top director partnerships and the genres they dominate.
-- ------------------------------------------------------------------------------
SELECT 
    td.director,
    COUNT(DISTINCT nt.show_id) AS total_titles,
    GROUP_CONCAT(DISTINCT nt.type) AS formats,
    GROUP_CONCAT(DISTINCT nt.primary_genre) AS genres
FROM title_directors td
JOIN netflix_titles nt ON td.show_id = nt.show_id
WHERE td.director != 'Unknown Director'
GROUP BY td.director
ORDER BY total_titles DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- Q7: Most Featured Lead Actors on the Platform
-- Business Context: High-impact actors driving global viewership and repeat casting.
-- ------------------------------------------------------------------------------
SELECT 
    tc.actor,
    COUNT(DISTINCT nt.show_id) AS appearances_count,
    SUM(CASE WHEN nt.type = 'Movie' THEN 1 ELSE 0 END) AS movie_appearances,
    SUM(CASE WHEN nt.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_appearances,
    GROUP_CONCAT(DISTINCT nt.primary_country) AS country_collaborations
FROM title_cast tc
JOIN netflix_titles nt ON tc.show_id = nt.show_id
WHERE tc.actor != 'Unknown Cast'
GROUP BY tc.actor
ORDER BY appearances_count DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Q8: Audience Demographics (Mature vs Teen vs Family)
-- Business Context: Evaluate content maturity profile for regulatory compliance and subscriber targeting.
-- ------------------------------------------------------------------------------
SELECT 
    age_group,
    COUNT(*) AS titles_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS catalog_share_pct,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_titles
GROUP BY age_group
ORDER BY titles_count DESC;


-- ------------------------------------------------------------------------------
-- Q9: Release Seasonality (Monthly Drop Patterns)
-- Business Context: Discover if additions spike in holiday months (July, Dec) to optimize marketing spend.
-- ------------------------------------------------------------------------------
SELECT 
    month_added,
    month_name_added,
    COUNT(*) AS total_additions,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_titles
GROUP BY month_added, month_name_added
ORDER BY month_added ASC;


-- ------------------------------------------------------------------------------
-- Q10: TV Shows Longevity: Top Series by Number of Seasons
-- Business Context: Identify multi-season franchises that maximize subscriber retention.
-- ------------------------------------------------------------------------------
SELECT 
    title,
    country,
    release_year,
    duration_num AS total_seasons,
    rating,
    listed_in AS genres
FROM netflix_titles
WHERE type = 'TV Show'
ORDER BY duration_num DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Q11: Movie Runtime Buckets and Optimization Zone
-- Business Context: Group movie durations into viewing segments to analyze consumer attention spans.
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN duration_num < 60 THEN '1. Short Film (<60 min)'
        WHEN duration_num BETWEEN 60 AND 90 THEN '2. Feature Lite (60-90 min)'
        WHEN duration_num BETWEEN 91 AND 120 THEN '3. Standard Feature (91-120 min)'
        WHEN duration_num BETWEEN 121 AND 150 THEN '4. Extended Feature (121-150 min)'
        ELSE '5. Epic (>150 min)'
    END AS duration_bucket,
    COUNT(*) AS movie_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'Movie'), 2) AS pct_of_movies,
    ROUND(AVG(duration_num), 1) AS avg_duration_mins
FROM netflix_titles
WHERE type = 'Movie' AND duration_num > 0
GROUP BY duration_bucket
ORDER BY duration_bucket ASC;


-- ------------------------------------------------------------------------------
-- Q12: Director-Actor Collaboration Duos (Frequent Partnerships)
-- Business Context: Uncover recurring creative teams that produce content together.
-- ------------------------------------------------------------------------------
SELECT 
    td.director,
    tc.actor,
    COUNT(DISTINCT td.show_id) AS collaborative_titles
FROM title_directors td
JOIN title_cast tc ON td.show_id = tc.show_id
WHERE td.director != 'Unknown Director' AND tc.actor != 'Unknown Cast'
GROUP BY td.director, tc.actor
HAVING collaborative_titles >= 3
ORDER BY collaborative_titles DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Q13: Internationalization Rate: Non-US vs US Content over Time
-- Business Context: Measure Netflix's transition from an American service to a global streaming titan.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS total_additions,
    SUM(CASE WHEN country_clean LIKE '%United States%' THEN 1 ELSE 0 END) AS us_involved_titles,
    SUM(CASE WHEN country_clean NOT LIKE '%United States%' AND country_clean != 'Unknown Country' THEN 1 ELSE 0 END) AS international_only_titles,
    ROUND(
        SUM(CASE WHEN country_clean NOT LIKE '%United States%' AND country_clean != 'Unknown Country' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) AS international_share_pct
FROM netflix_titles
WHERE year_added >= 2012
GROUP BY year_added
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- Q14: Multi-Genre Saturation Analysis
-- Business Context: Count how many genres are tagged per title (single vs multi-genre appeal).
-- ------------------------------------------------------------------------------
WITH genre_counts AS (
    SELECT 
        show_id,
        type,
        COUNT(genre) AS genres_tagged_count
    FROM title_genres
    GROUP BY show_id, type
)
SELECT 
    genres_tagged_count,
    type,
    COUNT(*) AS titles_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = gc.type), 2) AS pct_share
FROM genre_counts gc
GROUP BY genres_tagged_count, type
ORDER BY type, genres_tagged_count ASC;


-- ------------------------------------------------------------------------------
-- Q15: Top Ranked Country for Each Primary Genre (Window Function DENSE_RANK)
-- Business Context: Regional genre specializations (e.g. Anime in Japan, K-Dramas in South Korea).
-- ------------------------------------------------------------------------------
WITH country_genre_agg AS (
    SELECT 
        tg.genre,
        tc.country,
        COUNT(*) AS title_count,
        DENSE_RANK() OVER (PARTITION BY tg.genre ORDER BY COUNT(*) DESC) AS rank_in_genre
    FROM title_genres tg
    JOIN title_countries tc ON tg.show_id = tc.show_id
    WHERE tc.country != 'Unknown Country'
    GROUP BY tg.genre, tc.country
)
SELECT 
    genre,
    country AS top_producing_country,
    title_count
FROM country_genre_agg
WHERE rank_in_genre = 1
ORDER BY title_count DESC
LIMIT 20;
