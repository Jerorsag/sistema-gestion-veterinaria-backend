#!/bin/bash
# Script de configuración inicial para AWS Lightsail
# Este script debe ejecutarse UNA VEZ en la instancia nueva de Lightsail

set -e

echo "🔧 Configurando servidor AWS Lightsail para SGV..."

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar que es Ubuntu
if [ ! -f /etc/os-release ]; then
    echo "❌ Este script está diseñado para Ubuntu"
    exit 1
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
echo "📦 Instalando dependencias..."
sudo apt install -y \
    curl \
    git \
    unzip \
    nano \
    ufw

# Instalar Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${GREEN}✅ Docker ya está instalado${NC}"
fi

# Instalar Docker Compose
if ! docker compose version &> /dev/null; then
    echo "🐳 Instalando Docker Compose..."
    sudo apt install -y docker-compose-plugin
else
    echo -e "${GREEN}✅ Docker Compose ya está instalado${NC}"
fi

# Agregar usuario al grupo docker
echo "👤 Configurando permisos de Docker..."
sudo usermod -aG docker $USER

# Configurar firewall básico
echo "🔥 Configurando firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Backend (opcional, solo si necesitas acceso directo)

# Instalar Certbot para SSL (opcional)
read -p "¿Deseas instalar Certbot para SSL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔒 Instalando Certbot..."
    sudo apt install -y certbot python3-certbot-nginx
fi

# Instalar Nginx (para reverse proxy opcional)
read -p "¿Deseas instalar Nginx como reverse proxy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌐 Instalando Nginx..."
    sudo apt install -y nginx
    sudo systemctl enable nginx
fi

echo ""
echo -e "${GREEN}✅ Configuración inicial completada!${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "  1. Reinicia la sesión SSH o ejecuta: newgrp docker"
echo "  2. Clona tus repositorios"
echo "  3. Configura el archivo .env"
echo "  4. Ejecuta ./deploy-lightsail.sh"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Reinicia tu sesión SSH para que los cambios de grupo surtan efecto${NC}"

