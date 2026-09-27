# 📖 Netflix Analytics Data Dictionary

This document provides a comprehensive technical reference for the raw, transformed, and engineered features within the **Netflix Content Intelligence System**.

---

## 🏗️ 1. Main Fact Table (`netflix_titles`)

| Column Name | Raw / Engineered | Data Type | Nulls Allowed | Description | Sample Values |
|:---|:---|:---|:---|:---|:---|
| `show_id` | Raw | `VARCHAR(10)` | No (PK) | Unique identifier for each Netflix title | `"s1"`, `"s8807"` |
| `type` | Raw | `VARCHAR(20)` | No | Media format category | `"Movie"`, `"TV Show"` |
| `title` | Raw | `VARCHAR(255)` | No | Title name of the movie or television series | `"Stranger Things"`, `"Inception"` |
| `director` | Engineered (Clean) | `TEXT` | No | Directing talent (imputed `'Unknown Director'` if missing) | `"Christopher Nolan"`, `"Unknown Director"` |
| `cast` | Engineered (Clean) | `TEXT` | No | Comma-separated list of leading actors/actresses | `"Leonardo DiCaprio, Joseph Gordon-Levitt"` |
| `country` | Engineered (Clean) | `TEXT` | No | Production / co-production countries | `"United States, United Kingdom"` |
| `date_added` | Raw | `VARCHAR(50)` | Yes | Raw string date when title was added to Netflix | `"September 24, 2021"` |
| `date_added_dt` | Engineered | `TIMESTAMP` | No | Standardized ISO-8601 datetime format | `2021-09-24 00:00:00` |
| `release_year` | Raw | `INTEGER` | No | Theatrical release or television premiere year | `2019`, `2021` |
| `rating` | Engineered (Clean) | `VARCHAR(10)` | No | Official MPAA / TV Parental Guidelines age rating | `"TV-MA"`, `"PG-13"`, `"TV-14"` |
| `duration` | Raw | `VARCHAR(20)` | No | Raw duration representation string | `"90 min"`, `"3 Seasons"` |
| `duration_num` | Engineered | `INTEGER` | No | Extracted integer duration (minutes for movies, seasons for TV) | `90`, `3` |
| `duration_type` | Engineered | `VARCHAR(10)` | No | Unit classification of duration | `"min"`, `"Seasons"` |
| `listed_in` | Raw | `TEXT` | No | Comma-separated genres / categories | `"Dramas, International Movies"` |
| `description` | Raw | `TEXT` | Yes | Synopsis and editorial plot summary | `"As her father nears the end of his life..."` |
| `year_added` | Engineered | `INTEGER` | No | Extracted calendar year added to streaming library | `2021` |
| `month_added` | Engineered | `INTEGER` | No | Extracted calendar month number (1 to 12) | `9` |
| `month_name_added` | Engineered | `VARCHAR(15)` | No | Full month name added | `"September"` |
| `day_name_added` | Engineered | `VARCHAR(15)` | No | Day of week when title dropped on Netflix | `"Friday"` |
| `quarter_added` | Engineered | `INTEGER` | No | Fiscal / calendar quarter added (Q1 to Q4) | `3` |
| `target_audience` | Engineered | `VARCHAR(30)` | No | Granular audience segment mapped from rating | `"Mature Adults (18+)"`, `"Teens (13+)"` |
| `age_group` | Engineered | `VARCHAR(30)` | No | High-level demographic categorization | `"Adults (18+)"`, `"Kids & Family"` |
| `content_age_at_addition` | Engineered | `INTEGER` | No | Acquisition lag gap in years: `year_added - release_year` | `0` (Original/Day 1), `7` (Licensed Catalog) |
| `freshness_category` | Engineered | `VARCHAR(40)` | No | Strategic acquisition tier | `"Direct-to-Netflix / Same Year"`, `"Classic / Vintage (>10 yrs)"` |
| `primary_country` | Engineered | `VARCHAR(100)` | No | First listed dominant production country | `"United States"`, `"India"` |
| `primary_genre` | Engineered | `VARCHAR(100)` | No | First listed primary genre classification | `"Dramas"`, `"Comedies"` |

---

## 🔗 2. Normalized Relational OLAP Bridge Tables

### `title_genres` (Genre Dimension)
| Column Name | Data Type | Constraint | Description |
|:---|:---|:---|:---|
| `show_id` | `VARCHAR(10)` | FK -> `netflix_titles.show_id` | Foreign key referencing fact table |
| `genre` | `VARCHAR(100)` | Indexed | Individual unnested genre category |
| `type` | `VARCHAR(20)` | Indexed | Media format (`Movie` vs `TV Show`) |

### `title_countries` (Geographic Dimension)
| Column Name | Data Type | Constraint | Description |
|:---|:---|:---|:---|
| `show_id` | `VARCHAR(10)` | FK -> `netflix_titles.show_id` | Foreign key referencing fact table |
| `country` | `VARCHAR(100)` | Indexed | Individual unnested production country |
| `type` | `VARCHAR(20)` | Indexed | Media format (`Movie` vs `TV Show`) |

### `title_cast` (Talent & Actor Dimension)
| Column Name | Data Type | Constraint | Description |
|:---|:---|:---|:---|
| `show_id` | `VARCHAR(10)` | FK -> `netflix_titles.show_id` | Foreign key referencing fact table |
| `actor` | `VARCHAR(150)` | Indexed | Individual unnested actor/actress name |
| `type` | `VARCHAR(20)` | Indexed | Media format (`Movie` vs `TV Show`) |

### `title_directors` (Directing Talent Dimension)
| Column Name | Data Type | Constraint | Description |
|:---|:---|:---|:---|
| `show_id` | `VARCHAR(10)` | FK -> `netflix_titles.show_id` | Foreign key referencing fact table |
| `director` | `VARCHAR(150)` | Indexed | Individual unnested director name |
| `type` | `VARCHAR(20)` | Indexed | Media format (`Movie` vs `TV Show`) |

---

## 🛡️ 3. Anomaly Handling & Data Integrity Rules

1. **Rating-Duration Column Shift**: Repaired instances where duration strings (e.g. `74 min`) were wrongly populated in the `rating` attribute.
2. **Missing Dates Imputation**: Imputed missing `date_added` entries using the title's `release_year` + default Q1 release date.
3. **Categorical Imputation**: Replaced null directors, cast, and country entries with standardized `'Unknown ...'` sentinels to allow group-by queries without data loss.
4. **Relational Indexing**: B-tree indexes generated on `show_id`, `genre`, `country`, `actor`, and `director` for sub-millisecond query execution.
