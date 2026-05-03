import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import os
import tempfile


class GoldLayerProcessor:
    def __init__(self):
        DB_NAME = os.getenv("POSTGRES_DB", "postgres")
        DB_USER = os.getenv("POSTGRES_USER", "postgres")
        DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
        DB_HOST = os.getenv("DB_HOST", "db")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        self.engine = create_engine(DB_URL)
        base = Path(os.getenv("RAW_OUTPUT_PATH", "/app"))
        self.silver_path = base / "data" / "silver"

    def _get_latest_silver(self):
        partitions = sorted(self.silver_path.glob("*/*/*"))
        return partitions[-1] / "movies.parquet"

    def run(self):
        df = pd.read_parquet(self._get_latest_silver())

        df = self._prepare(df)

        self._merge_dimensions(df)
        self._merge_fact(df)

    def _prepare(self, df):

        df["profit"] = df["revenue"] - df["budget"]

        return df[[
            "id", "title", "release_date",
            "revenue", "budget", "profit",
            "vote_average", "vote_count", "popularity",
            "original_language", "status"
        ]].rename(columns={"id": "movie_id"})

    def _merge_dimensions(self, df):

        with self.engine.begin() as conn:

            languages = df["original_language"].dropna().unique().tolist()

            if languages:
                conn.execute(
                    text("""
                        INSERT INTO dim_language (language_code)
                        SELECT UNNEST(:languages)
                        ON CONFLICT (language_code) DO NOTHING
                    """),
                    {"languages": languages}
                )

            statuses = df["status"].dropna().unique().tolist()

            if statuses:
                conn.execute(
                    text("""
                        INSERT INTO dim_status (status)
                        SELECT UNNEST(:statuses)
                        ON CONFLICT (status) DO NOTHING
                    """),
                    {"statuses": statuses}
                )
    def _merge_fact(self, df):

        with self.engine.begin() as conn:

            dim_language = pd.read_sql("SELECT id, language_code FROM dim_language", conn)
            dim_status = pd.read_sql("SELECT id, status FROM dim_status", conn)

            df = df.merge(
                dim_language.rename(columns={"id": "dim_language_id"}),
                left_on="original_language",
                right_on="language_code",
                how="left"
            )

            df = df.merge(
                dim_status.rename(columns={"id": "dim_status_id"}),
                on="status",
                how="left"
            )

            fact_df = df[[
                "movie_id", "title", "release_date",
                "revenue", "budget", "profit",
                "vote_average", "vote_count", "popularity",
                "dim_language_id", "dim_status_id"
            ]]

            fact_df.to_sql("fact_movies_tmp", conn, if_exists="replace", index=False)

            conn.execute(text("""
                INSERT INTO fact_movies (
                    movie_id, title, release_date,
                    revenue, budget, profit,
                    vote_average, vote_count, popularity,
                    dim_language_id, dim_status_id
                )
                SELECT *
                FROM fact_movies_tmp
                ON CONFLICT (movie_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    release_date = EXCLUDED.release_date,
                    revenue = EXCLUDED.revenue,
                    budget = EXCLUDED.budget,
                    profit = EXCLUDED.profit,
                    vote_average = EXCLUDED.vote_average,
                    vote_count = EXCLUDED.vote_count,
                    popularity = EXCLUDED.popularity,
                    dim_language_id = EXCLUDED.dim_language_id,
                    dim_status_id = EXCLUDED.dim_status_id,
                    updated_at = CURRENT_TIMESTAMP
            """))

            conn.execute(text("DROP TABLE fact_movies_tmp"))