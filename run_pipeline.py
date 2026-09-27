"""
Master Execution Pipeline for Netflix Data Analytics Suite
Executes end-to-end data cleaning, SQL database construction, chart generation, and verification.
"""

import sys
import io
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.data_pipeline import NetflixDataPipeline
from src.eda_insights import NetflixEDAEngine
from src.recommender import NetflixRecommender
from src.db_manager import NetflixDBManager

def run_master_pipeline():
    print("=" * 70)
    print(">> NETFLIX DATA ANALYTICS & BUSINESS INTELLIGENCE PIPELINE")
    print("=" * 70)

    # 1. Run Data ETL Pipeline
    print("\n[Step 1/4] Running ETL Pipeline & Data Cleaning...")
    pipeline = NetflixDataPipeline()
    cleaned_df, csv_path, db_path = pipeline.run()
    print(f"[+] Data Pipeline Complete. Cleaned Records: {len(cleaned_df):,}")
    print(f"    - Cleaned CSV: {csv_path}")
    print(f"    - SQLite Database: {db_path}")

    # 2. Run EDA & Visual Insights Engine
    print("\n[Step 2/4] Generating Publication-Quality Figures & Calculating KPIs...")
    eda = NetflixEDAEngine(csv_path)
    kpis = eda.calculate_kpis()
    charts = eda.generate_all_charts()
    print(f"[+] Generated {len(charts)} high-resolution charts in reports/figures and images/")
    print(f"    - Total Catalog Titles: {kpis.get('total_titles'):,}")
    print(f"    - Movie vs TV Share: {kpis.get('pct_movies')}% Movies | {kpis.get('pct_tv')}% TV Shows")
    print(f"    - Top Producing Country: {kpis.get('top_country')}")
    print(f"    - Most In-Demand Genre: {kpis.get('top_genre')}")
    print(f"    - Average Movie Runtime: {kpis.get('avg_movie_duration_mins')} mins")

    # 3. Fit and Validate Recommender
    print("\n[Step 3/4] Initializing AI Recommendation Engine...")
    rec = NetflixRecommender()
    rec.fit(cleaned_df)
    sample_title = "Stranger Things" if "Stranger Things" in rec.get_all_titles() else rec.get_all_titles()[0]
    sample_recs = rec.recommend(sample_title, top_n=3)
    print(f"[+] Recommender initialized successfully! Sample recommendations for '{sample_title}':")
    for r in sample_recs:
        print(f"    - {r['title']} ({r['release_year']}) - Match: {r['similarity_score']}% | Type: {r['type']}")

    # 4. Validate SQL Database Engine
    print("\n[Step 4/4] Verifying SQL Analytics Studio...")
    db = NetflixDBManager(db_path)
    test_query = "SELECT type, count(*) as count FROM netflix_titles GROUP BY type;"
    test_res = db.execute_query(test_query)
    print(f"[+] SQL Engine response:\n{test_res.to_string(index=False)}")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL SYSTEMS OPERATIONAL AND READY FOR PRODUCTION / INTERVIEW DEMO!")
    print("=" * 70)
    print("\nQuick Launch Commands:")
    print("   1. Launch Interactive Web Dashboard:")
    print("      streamlit run app/streamlit_app.py")
    print("   2. Run Test Suite:")
    print("      pytest tests/")
    print("   3. Launch Jupyter Notebooks:")
    print("      jupyter notebook notebooks/02_Exploratory_Data_Analysis.ipynb\n")

if __name__ == "__main__":
    run_master_pipeline()
