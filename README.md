# Data Pipeline - Movies Dataset

Este projeto implementa um pipeline de engenharia de dados, processando um dataset de filmes desde a ingestão até a disponibilização em um Data Warehouse (PostgreSQL).

---

# 1. Arquitetura

## Fluxo de Dados

```text
Fonte (CSV - Kaggle)
        ↓
Python (RAW Layer)
        ↓
Parquet (SILVER Layer)
        ↓
PostgreSQL (GOLD Layer)
```

## Descrição
Fonte: Dataset CSV de filmes (Kaggle)
- RAW: Ingestão sem transformação
- SILVER: Limpeza, padronização e profiling
- GOLD: Modelagem dimensional (Star Schema) e carga no Postgres

# 2. Documentação da Tarefa
- Camada RAW

Responsabilidade:

Copiar dados brutos para o Data Lake
Organizar por partição de data (ano/mês/dia)

Saída:

data/raw/YYYY/MM/DD/dataset.csv
- Camada SILVER

Responsabilidade:

Limpeza de dados
Conversão de tipos
Tratamento de valores nulos
Remoção de duplicatas
Geração de profiling estatístico

Saída:

data/silver/YYYY/MM/DD/movies.parquet
data/silver/reports/ (relatórios)
- Camada GOLD

Responsabilidade:

Modelagem dimensional (Star Schema)
Carga incremental no Postgres
Uso de staging + COPY (alta performance)
UPSERT com ON CONFLICT

## Tabelas:

fact_movies
dim_language
dim_status

# 3. Dicionário de Dados
Coluna	Tipo	Descrição
id	int	Identificador único do filme
title	string	Nome do filme
vote_average	float	Média de avaliações
vote_count	int	Quantidade de votos
status	string	Status do filme (Released, etc.)
release_date	date	Data de lançamento
revenue	float	Receita total
runtime	int	Duração em minutos
adult	boolean	Indica conteúdo adulto
budget	float	Orçamento do filme
original_language	string	Idioma original
popularity	float	Score de popularidade
genres	string	Gêneros do filme
production_companies	string	Empresas produtoras

# 4. Qualidade de Dados

Durante o processamento na camada Silver, foram identificados os seguintes problemas:

- Valores nulos
title: alta quantidade de valores vazios
overview: alta quantidade de valores vazios
homepage: grande volume de dados ausentes
release_date: registros inválidos ou nulos
- Dados inconsistentes
adult: valores mistos (string e boolean)
runtime: valores nulos e não numéricos
budget e revenue: valores faltantes tratados como 0
- Duplicidade
Registros duplicados com mesmo id
- Strings problemáticas
Campos com valores:
"nan"
"[]"
"None"

# 5. Instruções de Execução
- 1. Clonar o projeto
git clone <repo>
cd <repo>
- 2. Instalar dependências (modo local)
pip install -r requirements.txt
- 3. Executar com Docker
docker-compose up --build
- 4. Ordem de execução do pipeline

O worker executa automaticamente:

1. RawLayerProcessor
2. SilverLayerProcessor
3. GoldLayerProcessor
🔹 6. Acessar o banco Postgres
docker exec -it <container_db> psql -U postgres

Exemplo:

SELECT COUNT(*) FROM fact_movies;
SELECT * FROM dim_language LIMIT 10;
## Exemplos de Queries
- Top filmes por lucro
SELECT
    m.movie_id,
    m.title,
    m.release_date,
    m.revenue,
    m.budget,
    m.profit
FROM dim_movies m
ORDER BY m.profit DESC
LIMIT 10;
```

- Quais gêneros têm, em média, maior avaliação (vote_average)?
```
SELECT
    g.genre_name,
    COUNT(DISTINCT m.movie_id) AS qtd_filmes,
    AVG(m.vote_average)        AS media_nota
FROM dim_movies m
JOIN bridge_movie_genre bg ON m.movie_id = bg.movie_id
JOIN dim_genre g          ON bg.genre_id = g.genre_id
GROUP BY g.genre_name
HAVING COUNT(DISTINCT m.movie_id) >= 5  
ORDER BY media_nota DESC;
```

- Por país de produção, qual o faturamento total e lucro médio dos filmes?

```
SELECT
    c.country_name,
    COUNT(DISTINCT m.movie_id) AS qtd_filmes,
    SUM(m.revenue)             AS receita_total,
    AVG(m.profit)              AS lucro_medio
FROM dim_movies m
JOIN bridge_movie_production_country bpc
    ON m.movie_id = bpc.movie_id
JOIN dim_production_country c
    ON bpc.production_country_id = c.country_id
GROUP BY c.country_name
ORDER BY receita_total DESC;
```

- Quais produtoras estão associadas aos filmes com maior retorno sobre investimento (ROI)?
```
SELECT
    pc.company_name,
    COUNT(DISTINCT m.movie_id)                               AS qtd_filmes,
    AVG(CASE WHEN m.budget > 0 THEN m.profit / m.budget END) AS roi_medio,
    SUM(m.profit)                                            AS lucro_total
FROM dim_movies m
JOIN bridge_movie_production_company bpc
    ON m.movie_id = bpc.movie_id
JOIN dim_production_company pc
    ON bpc.production_company_id = pc.company_id
GROUP BY pc.company_name
HAVING COUNT(DISTINCT m.movie_id) >= 5   -- opcional
ORDER BY roi_medio DESC;
```

- Evolução anual de faturamento e lucro por idioma original do filme

```
SELECT
    EXTRACT(YEAR FROM m.release_date) AS ano,
    l.language_code,
    COUNT(*)               AS qtd_filmes,
    SUM(m.revenue)         AS receita_total,
    SUM(m.profit)          AS lucro_total,
    AVG(m.vote_average)    AS nota_media
FROM dim_movies m
JOIN bridge_movie_language bl
    ON m.movie_id = bl.movie_id
JOIN dim_language l
    ON bl.language_id = l.language_id
WHERE m.release_date IS NOT NULL
GROUP BY ano, l.language_code
ORDER BY ano, receita_total DESC;
```