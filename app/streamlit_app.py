"""
Netflix Data Intelligence & Business Analytics Studio
Enterprise Interactive Streamlit Web Application
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os
import random

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.config import PROCESSED_DATA_PATH, DATABASE_PATH, NETFLIX_RED, NETFLIX_DARK_RED, NETFLIX_BLACK, NETFLIX_DARK_GRAY, NETFLIX_ACCENT_BLUE, NETFLIX_ACCENT_GOLD
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

# Custom CSS for Premium Netflix Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top, #1c1c1c 0%, #111111 60%, #0a0a0a 100%);
        color: #FFFFFF;
    }
    
    /* Header Bar */
    .header-banner {
        background: linear-gradient(90deg, rgba(229,9,20,0.15) 0%, rgba(20,20,20,0.8) 100%);
        border-left: 5px solid #E50914;
        border-radius: 8px;
        padding: 18px 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(229,9,20,0.25);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #E50914 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    h4, h5, h6 {
        color: #F5F5F1 !important;
        font-weight: 600 !important;
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2.0rem !important;
        font-weight: 800 !important;
        color: #E50914 !important;
        letter-spacing: -1px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.92rem !important;
        color: #CCCCCC !important;
        font-weight: 600;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
        color: #4CAF50 !important;
    }
    
    .metric-container {
        background: linear-gradient(145deg, #1f1f1f, #151515);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        border-color: rgba(229,9,20,0.4);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #141414;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #282828;
    }
    .stTabs [data-baseweb="tab"] {
        color: #B3B3B3;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E50914 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(229,9,20,0.4);
    }
    
    /* Recommendation Card */
    .rec-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #151515 100%);
        border: 1px solid #333333;
        border-left: 5px solid #E50914;
        padding: 20px;
        margin-bottom: 16px;
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.5);
        transition: all 0.25s ease;
    }
    .rec-card:hover {
        border-color: #E50914;
        box-shadow: 0 8px 25px rgba(229,9,20,0.25);
        transform: translateY(-2px);
    }
    .rec-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 6px;
    }
    .rec-badge-match {
        background: linear-gradient(90deg, #46d369, #2e9f4a);
        color: #000000;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 800;
        margin-right: 8px;
        display: inline-block;
    }
    .rec-badge-type {
        background-color: #E50914;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 6px;
        display: inline-block;
    }
    .rec-tag {
        background-color: #2b2b2b;
        color: #E5E5E5;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 6px;
        display: inline-block;
        border: 1px solid #3d3d3d;
    }
    .rec-reason {
        background-color: rgba(229,9,20,0.12);
        color: #FF7070;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(229,9,20,0.3);
        display: inline-block;
    }
    
    /* Talent Highlight Card */
    .talent-badge-card {
        background: linear-gradient(145deg, #222222, #181818);
        border: 1px solid #383838;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .talent-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 6px;
    }
    .talent-count {
        font-size: 1.4rem;
        font-weight: 800;
        color: #E50914;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DATA LOADING -----------------
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
    st.error(f"Error initializing Netflix Data Engine: {e}")
    st.stop()

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=180)
st.sidebar.markdown("### 🎛️ Dynamic Intelligence Filters")

# Reset Filters Action
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.session_state["content_type_filter"] = "All"
    st.session_state["year_range"] = (1990, int(df_raw['release_year'].max()))
    st.session_state["selected_countries"] = []
    st.session_state["selected_genres"] = []
    st.session_state["selected_age_groups"] = []
    st.rerun()

content_type_filter = st.sidebar.radio(
    "Content Type", 
    ["All", "Movie", "TV Show"], 
    horizontal=True, 
    key="content_type_filter"
)

# Year Range
min_year = int(df_raw['release_year'].min())
max_year = int(df_raw['release_year'].max())
year_range = st.sidebar.slider(
    "Release Year Range", 
    min_year, max_year, 
    st.session_state.get("year_range", (1990, max_year)),
    key="year_range"
)

# Country Filter (Safe Extraction)
all_countries = sorted([
    c.strip() for c in df_raw['country_clean'].astype(str).str.split(',').explode().unique() 
    if c and str(c).strip() not in ['Unknown Country', 'nan', '']
])
selected_countries = st.sidebar.multiselect(
    "Filter by Country", 
    all_countries, 
    default=st.session_state.get("selected_countries", []),
    key="selected_countries"
)

# Genre Filter
all_genres = sorted([
    g.strip() for g in df_raw['listed_in'].astype(str).str.split(',').explode().unique() 
    if g and str(g).strip() not in ['nan', '']
])
selected_genres = st.sidebar.multiselect(
    "Filter by Genre", 
    all_genres, 
    default=st.session_state.get("selected_genres", []),
    key="selected_genres"
)

# Age Demographics Filter
age_groups = sorted([a for a in df_raw['age_group'].dropna().unique().tolist() if a])
selected_age_groups = st.sidebar.multiselect(
    "Audience Age Segment", 
    age_groups, 
    default=st.session_state.get("selected_age_groups", []),
    key="selected_age_groups"
)

# ----------------- SAFE FILTER APPLICATION -----------------
filtered_df = df_raw.copy()

if content_type_filter != "All":
    filtered_df = filtered_df[filtered_df['type'] == content_type_filter]

filtered_df = filtered_df[
    (filtered_df['release_year'] >= year_range[0]) & 
    (filtered_df['release_year'] <= year_range[1])
]

if selected_countries:
    mask_c = filtered_df['country_clean'].apply(
        lambda c: any(sel.lower() in str(c).lower() for sel in selected_countries)
    )
    filtered_df = filtered_df[mask_c]

if selected_genres:
    mask_g = filtered_df['listed_in'].apply(
        lambda g: any(sel.lower() in str(g).lower() for sel in selected_genres)
    )
    filtered_df = filtered_df[mask_g]

if selected_age_groups:
    filtered_df = filtered_df[filtered_df['age_group'].isin(selected_age_groups)]

# Sidebar Status
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Titles:** `{len(filtered_df):,}` / `{len(df_raw):,}`")
st.sidebar.progress(len(filtered_df) / len(df_raw))
st.sidebar.markdown("💼 **Production Platform**: Netflix Data Intelligence Studio")

# ----------------- HEADER BANNER -----------------
st.markdown("""
<div class="header-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h2 style="margin: 0; padding: 0; color: #E50914;">🎬 NETFLIX DATA INTELLIGENCE & BUSINESS ANALYTICS</h2>
            <p style="margin: 4px 0 0 0; color: #CCCCCC; font-size: 1.05rem;">
                Enterprise-Grade Streaming Catalog Intelligence, Global Analytics, AI Recommender & SQL Studio
            </p>
        </div>
        <div style="background: rgba(229,9,20,0.2); border: 1px solid #E50914; padding: 6px 14px; border-radius: 20px; font-weight: 700; color: #FFFFFF; font-size: 0.85rem;">
            🟢 LIVE OLAP & ML ENGINE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- ZERO-DATA SAFEGUARD -----------------
if filtered_df.empty:
    st.warning("⚠️ **No titles match your current filter combination.** Please broaden your filter criteria or click the reset button below.")
    if st.button("🔄 Reset All Filters to Default", type="primary"):
        st.session_state["content_type_filter"] = "All"
        st.session_state["year_range"] = (1990, max_year)
        st.session_state["selected_countries"] = []
        st.session_state["selected_genres"] = []
        st.session_state["selected_age_groups"] = []
        st.rerun()
    st.stop()

# ----------------- TAB NAVIGATION -----------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Executive KPI Overview",
    "🌍 Global Production Intelligence",
    "🎭 Genre & Demographics",
    "⏱️ Runtimes & Seasonality",
    "🎬 Talent & Duos Network",
    "🤖 AI Content Recommender",
    "💾 SQL Analytics Studio",
    "📚 Catalog Browser & Inspector"
])

# ==============================================================================
# TAB 1: EXECUTIVE OVERVIEW
# ==============================================================================
with tab1:
    st.subheader("Platform Executive Key Performance Indicators")
    
    total_count = len(filtered_df)
    movie_count = len(filtered_df[filtered_df['type'] == 'Movie'])
    tv_count = len(filtered_df[filtered_df['type'] == 'TV Show'])
    movie_pct = round((movie_count / total_count * 100), 1) if total_count > 0 else 0
    tv_pct = round((tv_count / total_count * 100), 1) if total_count > 0 else 0
    
    movie_df = filtered_df[filtered_df['type'] == 'Movie']
    avg_runtime = round(movie_df['duration_num'].mean(), 1) if not movie_df.empty else 0
    
    top_country_series = filtered_df['primary_country'].replace('Unknown Country', np.nan).dropna()
    top_country_val = top_country_series.mode()[0] if not top_country_series.empty else "Global"

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Catalog Titles", f"{total_count:,}", f"{(total_count/len(df_raw)*100):.1f}% Active")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Movies Share", f"{movie_count:,}", f"{movie_pct}% Volume")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("TV Series Share", f"{tv_count:,}", f"{tv_pct}% Retention")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Avg Movie Runtime", f"{avg_runtime} min", "Sweet Spot")
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Top Content Hub", top_country_val, "Primary Volume")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("#### 📈 Netflix Catalog Growth Trajectory Over Time")
        growth_df = filtered_df[filtered_df['year_added'] >= 2008].groupby(['year_added', 'type']).size().reset_index(name='count')
        if not growth_df.empty:
            fig_growth = px.bar(
                growth_df, x='year_added', y='count', color='type',
                barmode='group',
                color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': NETFLIX_ACCENT_BLUE},
                labels={'year_added': 'Year Added to Platform', 'count': 'Titles Ingested', 'type': 'Format'}
            )
            fig_growth.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis=dict(showgrid=False, linecolor='#444'),
                yaxis=dict(showgrid=True, gridcolor='#222', linecolor='#444'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("No timeline data available for the current filter scope.")

    with col_chart2:
        st.markdown("#### 🍩 Content Type Split")
        fig_pie = px.pie(
            filtered_df, names='type',
            color='type',
            color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': '#0071EB'},
            hole=0.55
        )
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            marker=dict(line=dict(color='#141414', width=3))
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            font=dict(color='#E5E5E5'), 
            showlegend=False,
            annotations=[dict(text=f"<b>{total_count:,}</b><br>Titles", x=0.5, y=0.5, font_size=18, font_color="#FFFFFF", showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🌟 Flagship Titles in Current View")
    sample_showcase = filtered_df.sort_values(by=['year_added', 'release_year'], ascending=[False, False]).head(8)
    st.dataframe(
        sample_showcase[['title', 'type', 'release_year', 'rating_clean', 'duration', 'listed_in', 'primary_country', 'director_clean']],
        column_config={
            'title': 'Title',
            'type': 'Type',
            'release_year': 'Year',
            'rating_clean': 'Age Rating',
            'duration': 'Duration',
            'listed_in': 'Genres',
            'primary_country': 'Country',
            'director_clean': 'Director'
        },
        use_container_width=True,
        hide_index=True
    )

# ==============================================================================
# TAB 2: GLOBAL INTELLIGENCE
# ==============================================================================
with tab2:
    st.subheader("Geographic Footprint & Cross-Border Production Intelligence")
    
    # Unnest countries safely
    country_expanded = filtered_df.assign(
        country=filtered_df['country_clean'].astype(str).str.split(',')
    ).explode('country')
    country_expanded['country'] = country_expanded['country'].str.strip()
    country_expanded = country_expanded[~country_expanded['country'].isin(['Unknown Country', 'nan', ''])]

    if not country_expanded.empty:
        country_counts = country_expanded['country'].value_counts().reset_index()
        country_counts.columns = ['country', 'total_titles']

        # Interactive World Choropleth Map
        fig_map = px.choropleth(
            country_counts,
            locations='country',
            locationmode='country names',
            color='total_titles',
            hover_name='country',
            color_continuous_scale=[[0, '#2b1111'], [0.2, '#661111'], [0.5, NETFLIX_RED], [1.0, '#FF4B4B']],
            title="Global Content Production Heatmap (Titles Volume)"
        )
        fig_map.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False, showcoastlines=True, coastlinecolor='#444444', showland=True, landcolor='#1e1e1e'),
            font=dict(color='#E5E5E5'),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Top 10 Content Producing Countries")
            top10_c = country_counts.head(10)
            fig_top_c = px.bar(
                top10_c, x='total_titles', y='country', orientation='h',
                color='total_titles',
                color_continuous_scale=[[0, '#661111'], [1.0, NETFLIX_RED]]
            )
            fig_top_c.update_layout(
                yaxis=dict(autorange="reversed"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Catalog Count",
                yaxis_title="Country",
                showlegend=False
            )
            st.plotly_chart(fig_top_c, use_container_width=True)

        with col_g2:
            st.markdown("#### Movies vs TV Ratio in Top 10 Hubs")
            top10_names = top10_c['country'].tolist()
            c_ratio = country_expanded[country_expanded['country'].isin(top10_names)].groupby(['country', 'type']).size().reset_index(name='count')
            fig_c_ratio = px.bar(
                c_ratio, x='country', y='count', color='type',
                barmode='stack',
                color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': NETFLIX_ACCENT_BLUE}
            )
            fig_c_ratio.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Country",
                yaxis_title="Titles Count"
            )
            st.plotly_chart(fig_c_ratio, use_container_width=True)

        # Country Deep-Dive Spotlight
        st.markdown("---")
        st.markdown("### 🔍 Country Spotlight Deep Dive")
        spotlight_country = st.selectbox(
            "Select Country to Analyze Detailed Ecosystem:", 
            country_counts['country'].tolist(),
            index=0
        )

        c_titles = df_raw[df_raw['country_clean'].astype(str).str.contains(spotlight_country, regex=False, na=False)]
        c_movies = len(c_titles[c_titles['type'] == 'Movie'])
        c_tv = len(c_titles[c_titles['type'] == 'TV Show'])
        c_top_genre = c_titles['primary_genre'].mode()[0] if not c_titles['primary_genre'].empty else "N/A"

        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        with c_col1:
            st.metric(f"{spotlight_country} Total Titles", f"{len(c_titles):,}")
        with c_col2:
            st.metric("Movies Split", f"{c_movies:,} ({round(c_movies/max(1, len(c_titles))*100,1)}%)")
        with c_col3:
            st.metric("TV Series Split", f"{c_tv:,} ({round(c_tv/max(1, len(c_titles))*100,1)}%)")
        with c_col4:
            st.metric("Dominant Genre", c_top_genre)

        st.markdown(f"**Top Titles from {spotlight_country}:**")
        st.dataframe(
            c_titles[['title', 'type', 'release_year', 'rating_clean', 'duration', 'listed_in', 'director_clean']].head(6),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No country distribution data available for current selection.")

# ==============================================================================
# TAB 3: GENRE & DEMOGRAPHICS
# ==============================================================================
with tab3:
    st.subheader("Genre Dominance & Audience Demographic Targeting")
    
    genres_expanded = filtered_df.assign(
        genre=filtered_df['listed_in'].astype(str).str.split(',')
    ).explode('genre')
    genres_expanded['genre'] = genres_expanded['genre'].str.strip()
    genres_expanded = genres_expanded[genres_expanded['genre'] != '']

    col_gen1, col_gen2 = st.columns(2)

    with col_gen1:
        st.markdown("#### 🎭 Top 15 Most Dominant Genres")
        top_genres = genres_expanded['genre'].value_counts().head(15).reset_index()
        top_genres.columns = ['genre', 'count']
        fig_genres = px.bar(
            top_genres, x='count', y='genre', orientation='h',
            color='count',
            color_continuous_scale=[[0, '#444444'], [1.0, NETFLIX_RED]]
        )
        fig_genres.update_layout(
            yaxis=dict(autorange="reversed"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E5E5E5'),
            xaxis_title="Catalog Count",
            yaxis_title="Genre",
            showlegend=False
        )
        st.plotly_chart(fig_genres, use_container_width=True)

    with col_gen2:
        st.markdown("#### 🎯 Target Audience Demographics")
        age_counts = filtered_df['age_group'].value_counts().reset_index()
        age_counts.columns = ['age_group', 'count']
        fig_age = px.pie(
            age_counts, names='age_group', values='count',
            color='age_group',
            color_discrete_map={
                'Adults (18+)': NETFLIX_RED,
                'Teens (14+)': '#0071EB',
                'Older Kids (7+)': '#F5A623',
                'All Ages / Kids': '#4CAF50'
            },
            hole=0.45
        )
        fig_age.update_traces(textposition='inside', textinfo='percent+label')
        fig_age.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📊 Content Rating Distribution Matrix (TV-MA, TV-14, PG-13, R, etc.)")
    ratings_df = filtered_df.groupby(['rating_clean', 'type']).size().reset_index(name='count')
    fig_rat = px.bar(
        ratings_df, x='rating_clean', y='count', color='type',
        barmode='group',
        color_discrete_map={'Movie': NETFLIX_RED, 'TV Show': NETFLIX_ACCENT_BLUE},
        labels={'rating_clean': 'Official Content Rating', 'count': 'Volume'}
    )
    fig_rat.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E5E5E5'),
        xaxis_title="Rating Classification",
        yaxis_title="Total Titles"
    )
    st.plotly_chart(fig_rat, use_container_width=True)

# ==============================================================================
# TAB 4: RUNTIMES & SEASONALITY
# ==============================================================================
with tab4:
    st.subheader("Duration Distributions and Addition Seasonality Patterns")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### ⏱️ Movie Runtime Distribution (Minutes)")
        movie_subset = filtered_df[(filtered_df['type'] == 'Movie') & (filtered_df['duration_num'] > 0)]
        if not movie_subset.empty:
            fig_hist = px.histogram(
                movie_subset, x='duration_num', nbins=35,
                color_discrete_sequence=[NETFLIX_RED],
                marginal="box",
                labels={'duration_num': 'Duration (Minutes)'}
            )
            fig_hist.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Runtime (Minutes)",
                yaxis_title="Frequency"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No movie duration data in current filter selection.")

    with col_t2:
        st.markdown("#### 📺 TV Shows Longevity (Season Count)")
        tv_subset = filtered_df[(filtered_df['type'] == 'TV Show') & (filtered_df['duration_num'] > 0)]
        if not tv_subset.empty:
            season_counts = tv_subset['duration_num'].value_counts().reset_index()
            season_counts.columns = ['seasons', 'count']
            season_counts = season_counts.sort_values('seasons')
            fig_seasons = px.bar(
                season_counts, x='seasons', y='count',
                color_discrete_sequence=['#0071EB'],
                labels={'seasons': 'Number of Seasons', 'count': 'Number of Shows'}
            )
            fig_seasons.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E5E5E5'),
                xaxis_title="Total Seasons",
                yaxis_title="Number of TV Series"
            )
            st.plotly_chart(fig_seasons, use_container_width=True)
        else:
            st.info("No TV show season data in current filter selection.")

    st.markdown("---")
    st.markdown("#### 📅 Content Ingestion Seasonality (Month & Day Release Matrix)")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        monthly_data = filtered_df['month_name_added'].value_counts().reindex(month_order).fillna(0).reset_index()
        monthly_data.columns = ['month', 'count']
        fig_month = px.bar(
            monthly_data, x='month', y='count',
            color='count',
            color_continuous_scale=[[0, '#441111'], [1.0, NETFLIX_RED]],
            labels={'month': 'Month Added', 'count': 'Ingested Titles'}
        )
        fig_month.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'), showlegend=False)
        st.plotly_chart(fig_month, use_container_width=True)

    with col_m2:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_data = filtered_df['day_name_added'].value_counts().reindex(day_order).fillna(0).reset_index()
        daily_data.columns = ['day', 'count']
        fig_day = px.bar(
            daily_data, x='day', y='count',
            color_discrete_sequence=['#F5A623'],
            labels={'day': 'Day of Week', 'count': 'Ingested Titles'}
        )
        fig_day.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'))
        st.plotly_chart(fig_day, use_container_width=True)

# ==============================================================================
# TAB 5: TALENT & POWER DUOS NETWORK
# ==============================================================================
with tab5:
    st.subheader("Cast & Director Synergy Network Explorer")

    col_tal1, col_tal2 = st.columns(2)

    with col_tal1:
        st.markdown("#### 🎬 Top 10 Most Prolific Directors")
        directors_series = df_raw['director_clean'].astype(str).str.split(',').explode().str.strip()
        top_dirs = directors_series[~directors_series.isin(['Unknown Director', 'nan', ''])].value_counts().head(10).reset_index()
        top_dirs.columns = ['director', 'titles_count']
        fig_dirs = px.bar(
            top_dirs, x='titles_count', y='director', orientation='h',
            color='titles_count',
            color_continuous_scale=[[0, '#551111'], [1.0, NETFLIX_RED]]
        )
        fig_dirs.update_layout(yaxis=dict(autorange="reversed"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'), showlegend=False)
        st.plotly_chart(fig_dirs, use_container_width=True)

    with col_tal2:
        st.markdown("#### 🌟 Top 10 Most Featured Actors")
        actors_series = df_raw['cast_clean'].astype(str).str.split(',').explode().str.strip()
        top_acts = actors_series[~actors_series.isin(['Unknown Cast', 'nan', ''])].value_counts().head(10).reset_index()
        top_acts.columns = ['actor', 'titles_count']
        fig_acts = px.bar(
            top_acts, x='titles_count', y='actor', orientation='h',
            color='titles_count',
            color_continuous_scale=[[0, '#003366'], [1.0, '#0071EB']]
        )
        fig_acts.update_layout(yaxis=dict(autorange="reversed"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E5E5E5'), showlegend=False)
        st.plotly_chart(fig_acts, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Global Talent Filmography Search")
    
    st.markdown("Select a featured cinema icon or type any actor/director name:")
    
    chip_cols = st.columns(6)
    featured_stars = ["Shah Rukh Khan", "Leonardo DiCaprio", "Martin Scorsese", "Christopher Nolan", "Millie Bobby Brown", "Nawazuddin Siddiqui"]
    
    selected_chip = None
    for i, star in enumerate(featured_stars):
        with chip_cols[i]:
            if st.button(f"⭐ {star}", use_container_width=True):
                selected_chip = star

    search_query = st.text_input(
        "Enter Actor or Director Name:", 
        value=selected_chip if selected_chip else "Shah Rukh Khan"
    )

    if search_query:
        talent_results = df_raw[
            df_raw['cast_clean'].astype(str).str.contains(search_query, case=False, na=False) |
            df_raw['director_clean'].astype(str).str.contains(search_query, case=False, na=False)
        ]
        
        if not talent_results.empty:
            t_movies = len(talent_results[talent_results['type'] == 'Movie'])
            t_tv = len(talent_results[talent_results['type'] == 'TV Show'])
            min_yr = talent_results['release_year'].min()
            max_yr = talent_results['release_year'].max()

            st.success(f"🎬 **{search_query}** has **{len(talent_results)}** titles on Netflix ({t_movies} Movies, {t_tv} TV Shows) spanning {min_yr}–{max_yr}.")
            st.dataframe(
                talent_results[['title', 'type', 'release_year', 'rating_clean', 'duration', 'listed_in', 'primary_country', 'director_clean', 'description']],
                column_config={
                    'title': 'Title',
                    'type': 'Type',
                    'release_year': 'Year',
                    'rating_clean': 'Rating',
                    'duration': 'Duration',
                    'listed_in': 'Genres',
                    'primary_country': 'Country',
                    'director_clean': 'Director',
                    'description': 'Synopsis'
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"No titles found for '{search_query}'. Try searching other names like 'Adam Sandler', 'Robert De Niro', or 'Akshay Kumar'.")

# ==============================================================================
# TAB 6: AI CONTENT RECOMMENDER
# ==============================================================================
with tab6:
    st.subheader("🤖 AI Content Recommendation Engine (TF-IDF & Cosine Similarity)")
    st.markdown("Personalized streaming recommendations derived from high-dimensional metadata & synopsis vectors.")

    all_titles_list = recommender.get_all_titles()
    
    # Popular curated default picks
    popular_defaults = ["Stranger Things", "Squid Game", "Inception", "Breaking Bad", "Money Heist", "Peaky Blinders", "3 Idiots", "The Queen's Gambit", "Dark", "Narcos"]
    valid_popular = [p for p in popular_defaults if p in all_titles_list]
    default_title = valid_popular[0] if valid_popular else all_titles_list[0]

    col_r1, col_r2, col_r3, col_r4 = st.columns([3, 1, 1, 1])
    
    # Session state for title selection
    if "recommender_title" not in st.session_state:
        st.session_state["recommender_title"] = default_title

    with col_r1:
        current_idx = all_titles_list.index(st.session_state["recommender_title"]) if st.session_state["recommender_title"] in all_titles_list else 0
        selected_title = st.selectbox(
            "Select or Type Title from Catalog:", 
            all_titles_list, 
            index=current_idx,
            key="recommender_select"
        )
    with col_r2:
        top_n = st.slider("Results Count", min_value=3, max_value=12, value=6)
    with col_r3:
        filter_type_rec = st.selectbox("Format Filter", ["All Formats", "Movie", "TV Show"])
    with col_r4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🎲 Random Title", use_container_width=True):
            st.session_state["recommender_title"] = random.choice(valid_popular if valid_popular else all_titles_list)
            st.rerun()

    # Generate Recommendations automatically
    ftype = None if filter_type_rec == "All Formats" else filter_type_rec
    recommendations = recommender.recommend(selected_title, top_n=top_n, filter_type=ftype)

    st.markdown(f"### 🎯 Top Recommended Matches for *'{selected_title}'*:")
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"""
            <div class="rec-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div class="rec-title">{rec['title']} <span style="color: #888888; font-size: 1rem;">({rec['release_year']})</span></div>
                    <div>
                        <span class="rec-badge-match">{rec['similarity_score']}% Match</span>
                    </div>
                </div>
                <div style="margin: 8px 0;">
                    <span class="rec-badge-type">🎭 {rec['type']}</span>
                    <span class="rec-tag">⏱️ {rec['duration']}</span>
                    <span class="rec-tag">🔞 {rec['rating']}</span>
                    <span class="rec-tag">📍 {rec['country']}</span>
                    <span class="rec-reason">✨ {rec['match_reason']}</span>
                </div>
                <p style="color: #CCCCCC; font-size: 0.95rem; margin-top: 8px; margin-bottom: 4px;"><b>Genres:</b> {rec['genres']}</p>
                <p style="color: #AAAAAA; font-size: 0.9rem; margin-bottom: 6px;"><b>Director:</b> {rec['director']} | <b>Cast:</b> {rec['cast']}</p>
                <p style="color: #E5E5E5; font-style: italic; background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 6px; margin: 4px 0 0 0;">"{rec['description']}"</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No matching titles found for the specified format filter. Try switching format to 'All Formats'.")

# ==============================================================================
# TAB 7: SQL ANALYTICS STUDIO
# ==============================================================================
with tab7:
    st.subheader("💾 Interactive SQL Business Analytics Studio")
    st.markdown("Execute production SQL queries directly against the normalized relational SQLite database.")

    preset_dict = db_manager.get_preset_queries()
    
    col_sql1, col_sql2 = st.columns([3, 1])
    with col_sql1:
        selected_preset_name = st.selectbox("Choose a Pre-Engineered Business Analytics Query:", list(preset_dict.keys()))
    with col_sql2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        show_schema = st.checkbox("📋 Show DB Schema", value=False)

    if show_schema:
        tables_info = db_manager.get_tables_info()
        st.markdown("#### 🗄️ Relational Database Schema")
        schema_cols = st.columns(len(tables_info))
        for idx, (tbl_name, cols) in enumerate(tables_info.items()):
            with schema_cols[idx % len(schema_cols)]:
                st.markdown(f"**Table: `{tbl_name}`**")
                col_names = [f"- `{c['name']}` ({c['type']})" for c in cols]
                st.markdown("\n".join(col_names))
        st.markdown("---")

    preset_data = preset_dict[selected_preset_name]
    st.info(f"📌 **Business Analyst Objective:** {preset_data['description']}")

    # SQL Code Editor
    user_sql = st.text_area("SQL Query Editor (Edit or write your custom SQL):", value=preset_data['sql'].strip(), height=160)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_sql_btn = st.button("⚡ Execute SQL", type="primary")

    if run_sql_btn or user_sql:
        try:
            res_df = db_manager.execute_query(user_sql)
            st.success(f"Query executed successfully • Returned **{len(res_df)}** rows.")
            st.dataframe(res_df, use_container_width=True)

            # CSV Download
            csv_data = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export SQL Query Result (CSV)",
                data=csv_data,
                file_name=f"netflix_sql_{selected_preset_name.split('.')[0].strip()}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")

# ==============================================================================
# TAB 8: FULL CATALOG BROWSER & INSPECTOR
# ==============================================================================
with tab8:
    st.subheader("📚 Global Catalog Explorer & Title Inspector")
    st.markdown("Explore, search, and inspect the entire Netflix dataset with comprehensive metadata.")

    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        catalog_search = st.text_input("🔍 Quick Keyword Search (Title, Cast, Director, Genre):", placeholder="e.g. Marvel, Stranger Things, Bollywood, Comedy...")
    with col_b2:
        sort_by_col = st.selectbox("Sort By", ["Release Year (Newest)", "Release Year (Oldest)", "Date Added (Recent)", "Title (A-Z)"])

    browser_df = df_raw.copy()
    if catalog_search:
        s_mask = (
            browser_df['title'].astype(str).str.contains(catalog_search, case=False, na=False) |
            browser_df['cast_clean'].astype(str).str.contains(catalog_search, case=False, na=False) |
            browser_df['director_clean'].astype(str).str.contains(catalog_search, case=False, na=False) |
            browser_df['listed_in'].astype(str).str.contains(catalog_search, case=False, na=False) |
            browser_df['description'].astype(str).str.contains(catalog_search, case=False, na=False)
        )
        browser_df = browser_df[s_mask]

    if sort_by_col == "Release Year (Newest)":
        browser_df = browser_df.sort_values('release_year', ascending=False)
    elif sort_by_col == "Release Year (Oldest)":
        browser_df = browser_df.sort_values('release_year', ascending=True)
    elif sort_by_col == "Date Added (Recent)":
        browser_df = browser_df.sort_values('year_added', ascending=False)
    elif sort_by_col == "Title (A-Z)":
        browser_df = browser_df.sort_values('title', ascending=True)

    st.markdown(f"Displaying **{len(browser_df):,}** titles matching search:")
    
    st.dataframe(
        browser_df[['show_id', 'title', 'type', 'release_year', 'rating_clean', 'duration', 'listed_in', 'primary_country', 'director_clean', 'description']].head(100),
        column_config={
            'show_id': 'ID',
            'title': 'Title',
            'type': 'Type',
            'release_year': 'Year',
            'rating_clean': 'Rating',
            'duration': 'Duration',
            'listed_in': 'Genres',
            'primary_country': 'Country',
            'director_clean': 'Director',
            'description': 'Synopsis'
        },
        use_container_width=True,
        hide_index=True
    )

    # Download full catalog button
    full_csv = browser_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Catalog (CSV)",
        data=full_csv,
        file_name="netflix_catalog_export.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("<center style='color:#777777;'>🎬 Netflix Data Intelligence & Business Analytics Suite • Enterprise-Ready Data Science Portfolio</center>", unsafe_allow_html=True)
