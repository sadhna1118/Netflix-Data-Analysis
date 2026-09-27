"""
Netflix Data Intelligence & Business Analytics Studio
Interactive Streamlit Web Application
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.config import PROCESSED_DATA_PATH, DATABASE_PATH, NETFLIX_RED, NETFLIX_BLACK, NETFLIX_DARK_GRAY
from src.data_pipeline import NetflixDataPipeline
from src.recommender import NetflixRecommender
from src.db_manager import NetflixDBManager, BUSINESS_QUERIES

# Page Configuration
st.set_page_config(
    page_title="Netflix Business Intelligence & Analytics Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Netflix Aesthetic
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #141414;
        color: #FFFFFF;
    }
    .stApp {
        background-color: #141414;
    }
    /* Headers */
    h1, h2, h3 {
        color: #E50914 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
    }
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: bold !important;
        color: #E50914 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        color: #B3B3B3 !important;
    }
    .metric-card {
        background: linear-gradient(145deg, #1f1f1f, #181818);
        border: 1px solid #333333;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #181818;
        padding: 8px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #B3B3B3;
        font-weight: 600;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E50914 !important;
        color: #FFFFFF !important;
    }
    /* Recommendation Card */
    .rec-card {
        background-color: #1F1F1F;
        border-left: 4px solid #E50914;
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 6px;
    }
    .rec-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #FFFFFF;
    }
    .rec-badge {
        background-color: #E50914;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 6px;
    }
    .rec-tag {
        background-color: #333333;
        color: #E5E5E5;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not PROCESSED_DATA_PATH.exists():
        pipeline = NetflixDataPipeline()
        df, _, _ = pipeline.run()
        return df
    return pd.read_csv(PROCESSED_DATA_PATH)

@st.cache_resource
def load_recommender(df):
    rec = NetflixRecommender()
    rec.fit(df)
    return rec

try:
    df_raw = load_data()
    recommender = load_recommender(df_raw)
    db_manager = NetflixDBManager()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=180)
st.sidebar.markdown("### 🎛️ Dynamic Analysis Filters")

content_type_filter = st.sidebar.radio("Content Type", ["All", "Movie", "TV Show"], horizontal=True)

# Year Range
min_year = int(df_raw['release_year'].min())
max_year = int(df_raw['release_year'].max())
year_range = st.sidebar.slider("Release Year Range", min_year, max_year, (1990, max_year))

# Country Filter
all_countries = sorted([c.strip() for c in df_raw['country_clean'].str.split(',').explode().unique() if c and c != 'Unknown Country'])
selected_countries = st.sidebar.multiselect("Filter by Country", all_countries, default=[])

# Genre Filter
all_genres = sorted([g.strip() for g in df_raw['listed_in'].str.split(',').explode().unique() if g])
selected_genres = st.sidebar.multiselect("Filter by Genre", all_genres, default=[])

# Age Demographics Filter
age_groups = sorted(df_raw['age_group'].unique().tolist())
selected_age_groups = st.sidebar.multiselect("Audience Age Segment", age_groups, default=[])

# Apply Filters
filtered_df = df_raw.copy()

if content_type_filter != "All":
    filtered_df = filtered_df[filtered_df['type'] == content_type_filter]

filtered_df = filtered_df[
    (filtered_df['release_year'] >= year_range[0]) & 
    (filtered_df['release_year'] <= year_range[1])
]

if selected_countries:
    pattern = '|'.join([f"\\b{c}\\b" for c in selected_countries])
    filtered_df = filtered_df[filtered_df['country_clean'].str.contains(pattern, regex=True, na=False)]

if selected_genres:
    pattern = '|'.join([f"\\b{g}\\b" for g in selected_genres])
    filtered_df = filtered_df[filtered_df['listed_in'].str.contains(pattern, regex=True, na=False)]

if selected_age_groups:
    filtered_df = filtered_df[filtered_df['age_group'].isin(selected_age_groups)]

# Sidebar Summary Info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Titles:** `{len(filtered_df):,}` / `{len(df_raw):,}`")
st.sidebar.markdown("💼 **Portfolio Ready**: Real-Life Data Analyst Tool")

# ----------------- MAIN CONTENT -----------------
st.title("🎬 Netflix Data Intelligence & Analytics Suite")
st.markdown("##### *Enterprise-Grade Exploratory Data Analysis, SQL Studio, & Content Recommender*")

# TAB NAVIGATION
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Executive KPI Overview",
    "🌍 Global Intelligence",
    "🎭 Genre & Demographics",
    "⏱️ Runtimes & Seasonality",
    "🎬 Talent & Duos Explorer",
    "🤖 AI Content Recommender",
    "💾 SQL Analytics Studio"
])

# ----------------- TAB 1: EXECUTIVE OVERVIEW -----------------
with tab1:
    st.subheader("Platform Executive Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    total_count = len(filtered_df)
    movie_count = len(filtered_df[filtered_df['type'] == 'Movie'])
    tv_count = len(filtered_df[filtered_df['type'] == 'TV Show'])
    movie_pct = round((movie_count / total_count * 100), 1) if total_count > 0 else 0
    tv_pct = round((tv_count / total_count * 100), 1) if total_count > 0 else 0
    avg_runtime = round(filtered_df[filtered_df['type'] == 'Movie']['duration_num'].mean(), 1)

    with col1:
        st.metric("Total Catalog Titles", f"{total_count:,}")
    with col2:
        st.metric("Movies Split", f"{movie_count:,} ({movie_pct}%)")
    with col3:
        st.metric("TV Shows Split", f"{tv_count:,} ({tv_pct}%)")
    with col4:
        st.metric("Avg Movie Runtime", f"{avg_runtime} min")
    with col5:
        top_c = filtered_df['primary_country'].mode()[0] if not filtered_df.empty else "N/A"
        st.metric("Top Producing Hub", top_c)

    st.markdown("---")

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("#### 📈 Netflix Catalog Growth Over Time (Year Added)")
        growth_df = filtered_df[filtered_df['year_added'] >= 2008].groupby(['year_added', 'type']).size().reset_index(name='count')
        if not growth_df.empty:
            fig_growth = px.bar(
                growth_df, x='year_added', y='count', color='type',
                barmode='group',
                color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#0071EB'},
                labels={'year_added': 'Year Added to Platform', 'count': 'Titles Added', 'type': 'Content Type'}
            )
            fig_growth.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")

    with col_chart2:
        st.markdown("#### 🍩 Content Type Distribution")
        if total_count > 0:
            fig_pie = px.pie(
                filtered_df, names='type',
                color='type',
                color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#221F1F'},
                hole=0.45
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data to display.")

# ----------------- TAB 2: GLOBAL INTELLIGENCE -----------------
with tab2:
    st.subheader("Geographic Footprint & International Production Analysis")
    
    # Unnest countries
    country_expanded = filtered_df.assign(
        country=filtered_df['country_clean'].str.split(',')
    ).explode('country')
    country_expanded['country'] = country_expanded['country'].str.strip()
    country_expanded = country_expanded[~country_expanded['country'].isin(['Unknown Country', ''])]

    if not country_expanded.empty:
        country_counts = country_expanded['country'].value_counts().reset_index()
        country_counts.columns = ['country', 'total_titles']

        # Interactive World Map
        fig_map = px.choropleth(
            country_counts,
            locations='country',
            locationmode='country names',
            color='total_titles',
            hover_name='country',
            color_continuous_scale=[[0, '#331111'], [0.2, '#771111'], [0.5, NETFLIX_RED], [1.0, '#FF4B4B']],
            title="Global Title Distribution Heatmap"
        )
        fig_map.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False, showcoastlines=True, coastlinecolor='#444444'),
            font=dict(color='#E5E5E5')
        )
        st.plotly_chart(fig_map, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Top 10 Content Producing Countries")
            top10_c = country_counts.head(10)
            fig_top_c = px.bar(
                top10_c, x='total_titles', y='country', orientation='h',
                color_discrete_sequence=[NETFLIX_RED]
            )
            fig_top_c.update_layout(
                yaxis=dict(autorange="reversed"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Titles Count",
                yaxis_title="Country"
            )
            st.plotly_chart(fig_top_c, use_container_width=True)

        with col_g2:
            st.markdown("#### Movies vs TV Ratio in Top 10 Countries")
            top10_names = top10_c['country'].tolist()
            c_ratio = country_expanded[country_expanded['country'].isin(top10_names)].groupby(['country', 'type']).size().reset_index(name='count')
            fig_c_ratio = px.bar(
                c_ratio, x='country', y='count', color='type',
                barmode='stack',
                color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#0071EB'}
            )
            fig_c_ratio.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Country",
                yaxis_title="Titles"
            )
            st.plotly_chart(fig_c_ratio, use_container_width=True)
    else:
        st.info("No country information available for current selection.")

# ----------------- TAB 3: GENRE & DEMOGRAPHICS -----------------
with tab3:
    st.subheader("Genre Dominance & Audience Demographic Targeting")
    
    genres_expanded = filtered_df.assign(
        genre=filtered_df['listed_in'].str.split(',')
    ).explode('genre')
    genres_expanded['genre'] = genres_expanded['genre'].str.strip()

    col_gen1, col_gen2 = st.columns(2)

    with col_gen1:
        st.markdown("#### 🎭 Top 15 Most Popular Genres")
        top_genres = genres_expanded['genre'].value_counts().head(15).reset_index()
        top_genres.columns = ['genre', 'count']
        fig_genres = px.bar(
            top_genres, x='count', y='genre', orientation='h',
            color='count',
            color_continuous_scale=[[0, '#555555'], [1.0, NETFLIX_RED]]
        )
        fig_genres.update_layout(
            yaxis=dict(autorange="reversed"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E5E5E5'),
            showlegend=False
        )
        st.plotly_chart(fig_genres, use_container_width=True)

    with col_gen2:
        st.markdown("#### 🎯 Audience Target Demographics")
        age_counts = filtered_df['age_group'].value_counts().reset_index()
        age_counts.columns = ['age_group', 'count']
        fig_age = px.pie(
            age_counts, names='age_group', values='count',
            color='age_group',
            color_discrete_sequence=[NETFLIX_RED, '#E57373', '#757575', '#221F1F'],
            hole=0.4
        )
        fig_age.update_traces(textposition='inside', textinfo='percent+label')
        fig_age.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📊 Content Ratings Breakdown (TV-MA, TV-14, PG-13, etc.)")
    ratings_df = filtered_df['rating_clean'].value_counts().reset_index()
    ratings_df.columns = ['rating', 'count']
    fig_rat = px.bar(
        ratings_df, x='rating', y='count',
        color='count',
        color_continuous_scale=[[0, '#444444'], [1.0, NETFLIX_RED]]
    )
    fig_rat.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E5E5E5'),
        xaxis_title="Content Rating",
        yaxis_title="Total Titles"
    )
    st.plotly_chart(fig_rat, use_container_width=True)

# ----------------- TAB 4: RUNTIMES & SEASONALITY -----------------
with tab4:
    st.subheader("Duration Distributions and Addition Seasonality Patterns")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### ⏱️ Movie Runtime Distribution (in Minutes)")
        movie_subset = filtered_df[(filtered_df['type'] == 'Movie') & (filtered_df['duration_num'] > 0)]
        if not movie_subset.empty:
            fig_hist = px.histogram(
                movie_subset, x='duration_num', nbins=40,
                color_discrete_sequence=[NETFLIX_RED],
                marginal="box",
                labels={'duration_num': 'Duration (Minutes)'}
            )
            fig_hist.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                yaxis_title="Frequency"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No movies in current selection.")

    with col_t2:
        st.markdown("#### 📺 TV Shows Season Longevity Distribution")
        tv_subset = filtered_df[(filtered_df['type'] == 'TV Show') & (filtered_df['duration_num'] > 0)]
        if not tv_subset.empty:
            season_counts = tv_subset['duration_num'].value_counts().reset_index()
            season_counts.columns = ['seasons', 'count']
            season_counts = season_counts.sort_values('seasons')
            fig_seasons = px.bar(
                season_counts, x='seasons', y='count',
                color_discrete_sequence=['#0071EB'],
                labels={'seasons': 'Number of Seasons', 'count': 'Number of TV Shows'}
            )
            fig_seasons.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5')
            )
            st.plotly_chart(fig_seasons, use_container_width=True)
        else:
            st.info("No TV shows in current selection.")

    st.markdown("---")
    st.markdown("#### 📅 Monthly & Day-of-Week Content Release Patterns")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        monthly_data = filtered_df['month_name_added'].value_counts().reindex(month_order).fillna(0).reset_index()
        monthly_data.columns = ['month', 'count']
        fig_month = px.bar(
            monthly_data, x='month', y='count',
            color_discrete_sequence=[NETFLIX_RED],
            labels={'month': 'Month Added', 'count': 'Titles Added'}
        )
        fig_month.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
        st.plotly_chart(fig_month, use_container_width=True)

    with col_m2:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_data = filtered_df['day_name_added'].value_counts().reindex(day_order).fillna(0).reset_index()
        daily_data.columns = ['day', 'count']
        fig_day = px.bar(
            daily_data, x='day', y='count',
            color_discrete_sequence=['#F5A623'],
            labels={'day': 'Day of Week', 'count': 'Titles Added'}
        )
        fig_day.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
        st.plotly_chart(fig_day, use_container_width=True)

# ----------------- TAB 5: TALENT & DUOS EXPLORER -----------------
with tab5:
    st.subheader("Cast & Director Synergy Network Explorer")

    col_tal1, col_tal2 = st.columns(2)

    with col_tal1:
        st.markdown("#### 🎬 Top 10 Most Prolific Directors")
        directors_series = filtered_df['director_clean'].str.split(',').explode().str.strip()
        top_dirs = directors_series[~directors_series.isin(['Unknown Director', ''])].value_counts().head(10).reset_index()
        top_dirs.columns = ['director', 'titles_count']
        if not top_dirs.empty:
            fig_dirs = px.bar(
                top_dirs, x='titles_count', y='director', orientation='h',
                color_discrete_sequence=[NETFLIX_RED]
            )
            fig_dirs.update_layout(yaxis=dict(autorange="reversed"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
            st.plotly_chart(fig_dirs, use_container_width=True)

    with col_tal2:
        st.markdown("#### 🌟 Top 10 Most Featured Actors")
        actors_series = filtered_df['cast_clean'].str.split(',').explode().str.strip()
        top_acts = actors_series[~actors_series.isin(['Unknown Cast', ''])].value_counts().head(10).reset_index()
        top_acts.columns = ['actor', 'titles_count']
        if not top_acts.empty:
            fig_acts = px.bar(
                top_acts, x='titles_count', y='actor', orientation='h',
                color_discrete_sequence=['#0071EB']
            )
            fig_acts.update_layout(yaxis=dict(autorange="reversed"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
            st.plotly_chart(fig_acts, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔍 Search Talent Filmography")
    search_person = st.text_input("Enter Actor or Director Name (e.g., Leonardo DiCaprio, Shah Rukh Khan, Christopher Nolan, Martin Scorsese):")
    if search_person:
        talent_results = filtered_df[
            filtered_df['cast_clean'].str.contains(search_person, case=False, na=False) |
            filtered_df['director_clean'].str.contains(search_person, case=False, na=False)
        ]
        if not talent_results.empty:
            st.success(f"Found {len(talent_results)} titles involving **{search_person}**:")
            st.dataframe(
                talent_results[['title', 'type', 'release_year', 'rating', 'duration', 'listed_in', 'country_clean']],
                use_container_width=True
            )
        else:
            st.warning(f"No titles found for '{search_person}'.")

# ----------------- TAB 6: AI CONTENT RECOMMENDER -----------------
with tab6:
    st.subheader("🤖 AI Content Recommendation Engine (TF-IDF + Cosine Similarity)")
    st.markdown("Discover similar movies and TV shows based on deep textual and metadata similarity.")

    all_titles_list = recommender.get_all_titles()
    
    col_r1, col_r2, col_r3 = st.columns([3, 1, 1])
    with col_r1:
        selected_title = st.selectbox("Select or Type a Title from Netflix Catalog:", all_titles_list, index=0)
    with col_r2:
        top_n = st.slider("Recommendations Count", min_value=3, max_value=12, value=6)
    with col_r3:
        filter_type_rec = st.selectbox("Filter Match Type", ["All Types", "Movie", "TV Show"])

    if st.button("🚀 Generate AI Recommendations", type="primary"):
        with st.spinner("Analyzing high-dimensional feature vectors..."):
            ftype = None if filter_type_rec == "All Types" else filter_type_rec
            recommendations = recommender.recommend(selected_title, top_n=top_n, filter_type=ftype)

            if recommendations:
                st.markdown(f"### 🎯 Top Matches for *{selected_title}*:")
                for rec in recommendations:
                    st.markdown(f"""
                    <div class="rec-card">
                        <div class="rec-title">{rec['title']} ({rec['release_year']})</div>
                        <div style="margin: 8px 0;">
                            <span class="rec-badge">{rec['similarity_score']}% Match</span>
                            <span class="rec-tag">🎭 {rec['type']}</span>
                            <span class="rec-tag">⏱️ {rec['duration']}</span>
                            <span class="rec-tag">🔞 {rec['rating']}</span>
                            <span class="rec-tag">📍 {rec['country']}</span>
                        </div>
                        <p style="color: #CCCCCC; font-size: 0.95rem; margin-top: 6px;"><b>Genres:</b> {rec['genres']}</p>
                        <p style="color: #CCCCCC; font-size: 0.95rem;"><b>Director:</b> {rec['director']} | <b>Cast:</b> {rec['cast']}</p>
                        <p style="color: #E5E5E5; font-style: italic; margin-top: 4px;">"{rec['description']}"</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No close recommendations found.")

# ----------------- TAB 7: SQL ANALYTICS STUDIO -----------------
with tab7:
    st.subheader("💾 Interactive SQL Analytics Studio")
    st.markdown("Execute business intelligence queries against the relational SQLite database.")

    col_sql1, col_sql2 = st.columns([2, 1])
    
    preset_dict = db_manager.get_preset_queries()
    with col_sql1:
        selected_preset_name = st.selectbox("Choose a Pre-Formulated Business Question:", list(preset_dict.keys()))
    
    preset_data = preset_dict[selected_preset_name]
    st.info(f"📌 **Business Objective:** {preset_data['description']}")

    # SQL Code Editor Area
    user_sql = st.text_area("SQL Query Editor (Edit or write your custom SQL):", value=preset_data['sql'].strip(), height=160)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_sql_btn = st.button("⚡ Run SQL Query", type="primary")

    if run_sql_btn or user_sql:
        try:
            res_df = db_manager.execute_query(user_sql)
            st.success(f"Query returned **{len(res_df)}** rows successfully.")
            st.dataframe(res_df, use_container_width=True)

            # CSV Download Option
            csv_data = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Query Results (CSV)",
                data=csv_data,
                file_name=f"netflix_sql_result.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"SQL Error: {e}")

st.markdown("---")
st.markdown("<center style='color:#777777;'>Netflix Data Intelligence Platform • Built for Real-Life Data Analyst Portfolio & Business Strategy</center>", unsafe_allow_html=True)
