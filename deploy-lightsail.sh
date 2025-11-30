#!/bin/bash
# Script de despliegue automatizado para AWS Lightsail
# Uso: ./deploy-lightsail.sh

set -e

echo "🚀 Iniciando despliegue en AWS Lightsail..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.prod.yml no encontrado${NC}"
    echo "Por favor, ejecuta este script desde el directorio del backend"
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "Creando .env desde .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Por favor, edita el archivo .env con tus valores antes de continuar${NC}"
        exit 1
    else
        echo -e "${RED}❌ Error: .env.example no encontrado${NC}"
        exit 1
    fi
fi

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado${NC}"
    exit 1
fi

# Verificar que Docker Compose está instalado
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-requisitos verificados${NC}"

# Preguntar si se quiere hacer pull del código
read -p "¿Deseas actualizar el código desde Git? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Actualizando código desde Git..."
    git pull || echo -e "${YELLOW}⚠️  No se pudo hacer git pull (puede ser normal si no hay cambios)${NC}"
fi

# Preguntar si se quiere construir las imágenes
read -p "¿Deseas reconstruir las imágenes Docker? (y/n) " -n 1 -r
echo
BUILD_FLAG=""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    BUILD_FLAG="--build"
    echo "🔨 Reconstruyendo imágenes..."
fi

# Detener contenedores existentes
echo "🛑 Deteniendo contenedores existentes..."
docker compose -f docker-compose.prod.yml down || true

# Levantar contenedores
echo "🚀 Iniciando contenedores..."
docker compose -f docker-compose.prod.yml up -d $BUILD_FLAG

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado de los contenedores
echo "📊 Estado de los contenedores:"
docker compose -f docker-compose.prod.yml ps

# Verificar salud de los servicios
echo ""
echo "🏥 Verificando salud de los servicios..."

# Verificar base de datos
if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Base de datos: OK${NC}"
else
    echo -e "${RED}❌ Base de datos: ERROR${NC}"
fi

# Verificar backend
if curl -f http://localhost:8000/api/v1/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: OK${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: No responde (puede estar iniciando)${NC}"
fi

# Verificar frontend
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: OK${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: No responde (puede estar iniciando)${NC}"
fi

echo ""
echo -e "${GREEN}✅ Despliegue completado!${NC}"
echo ""
echo "📝 Comandos útiles:"
echo "  - Ver logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  - Ver estado: docker compose -f docker-compose.prod.yml ps"
echo "  - Detener: docker compose -f docker-compose.prod.yml down"
echo "  - Reiniciar: docker compose -f docker-compose.prod.yml restart"
echo ""

