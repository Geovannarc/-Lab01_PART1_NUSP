#!/bin/sh

echo "aguardando banco de dados..."

until pg_isready -h db -p 5432 -U postgres
do
  sleep 2
done

echo "criando schema..."

psql postgresql://postgres:postgres@db:5432/postgres -f /app/sql/schema.sql

echo "executando pipeline..."

python -m worker