#!/bin/bash
set -e

echo "🚀 Iniciando Sistema de Gestión Veterinaria Backend..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté disponible..."
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_NAME:-sgv}

while ! python -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', user='$DB_USER', password='$DB_PASSWORD', dbname='$DB_NAME')" 2>/dev/null; do
  echo "⏳ Base de datos no disponible aún, esperando..."
  sleep 2
done

echo "✅ Base de datos disponible!"

# Ejecutar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos (si es necesario)
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear || echo "⚠️  No hay archivos estáticos para recopilar"

# Si se pasa un comando personalizado (no gunicorn), ejecutarlo
if [ "$1" != "gunicorn" ] && [ -n "$1" ]; then
    echo "🔧 Ejecutando comando personalizado: $@"
    exec "$@"
    exit
fi

# Ejecutar el servidor (gunicorn por defecto)
echo "🌐 Iniciando servidor Gunicorn..."
exec "$@"

