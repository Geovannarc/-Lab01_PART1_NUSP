CREATE TABLE IF NOT EXISTS dim_language (
    language_id SERIAL PRIMARY KEY,
    language_code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_production_company (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_production_country (
    country_id SERIAL PRIMARY KEY,
    country_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_movies (
    movie_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    release_date DATE,
    revenue NUMERIC,
    budget NUMERIC,
    profit NUMERIC,
    vote_average NUMERIC,
    vote_count INT,
    popularity NUMERIC,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bridge_movie_genre (
    movie_id INT NOT NULL REFERENCES dim_movies(movie_id),
    genre_id INT NOT NULL REFERENCES dim_genre(genre_id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE IF NOT EXISTS bridge_movie_language (
    movie_id INT NOT NULL REFERENCES dim_movies(movie_id),
    language_id INT NOT NULL REFERENCES dim_language(language_id),
    PRIMARY KEY (movie_id, language_id)
);

CREATE TABLE IF NOT EXISTS bridge_movie_production_company (
    movie_id INT NOT NULL REFERENCES dim_movies(movie_id),
    production_company_id INT NOT NULL REFERENCES dim_production_company(company_id),
    PRIMARY KEY (movie_id, production_company_id)
);

CREATE TABLE IF NOT EXISTS bridge_movie_production_country (
    movie_id INT NOT NULL REFERENCES dim_movies(movie_id),
    production_country_id INT NOT NULL REFERENCES dim_production_country(country_id),
    PRIMARY KEY (movie_id, production_country_id)
);