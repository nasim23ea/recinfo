#!/bin/bash

# ==============================================================================
# Script de Inicio para Agente de IA Shopify
# ==============================================================================

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "================================================================"
echo "🤖 AGENTE DE IA PARA SHOPIFY - INICIO"
echo "================================================================"

# Verificar que estemos en el directorio correcto
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "No se encontró docker-compose.yml. Asegúrate de ejecutar este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar si Docker está instalado y ejecutándose
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker no está ejecutándose. Por favor inicia Docker primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Verificar archivo .env
if [[ ! -f ".env" ]]; then
    print_warning "Archivo .env no encontrado. Copiando desde .env.example..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_warning "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales antes de continuar."
        read -p "¿Has configurado el archivo .env? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Por favor configura el archivo .env primero."
            exit 1
        fi
    else
        print_error "No se encontró .env.example. Crea un archivo .env manualmente."
        exit 1
    fi
fi

# Verificar datos deportivos
if [[ ! -f "equipos.txt" ]] || [[ ! -f "partidos.txt" ]]; then
    print_warning "Archivos de datos deportivos no encontrados."
    print_status "Los archivos equipos.txt y partidos.txt son necesarios para el funcionamiento completo."
fi

# Función para verificar si un servicio está saludable
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Esperando que $service_name esté listo..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps $service_name | grep -q "healthy\|Up"; then
            print_success "$service_name está listo!"
            return 0
        fi
        
        print_status "Intento $attempt/$max_attempts - Esperando $service_name..."
        sleep 5
        ((attempt++))
    done
    
    print_error "$service_name no pudo iniciarse correctamente."
    return 1
}

# Función para mostrar logs en tiempo real
show_logs() {
    print_status "Mostrando logs en tiempo real (Ctrl+C para salir)..."
    docker-compose logs -f backend
}

# Función para detener servicios
stop_services() {
    print_status "Deteniendo servicios..."
    docker-compose down
    print_success "Servicios detenidos."
}

# Función para reiniciar servicios
restart_services() {
    print_status "Reiniciando servicios..."
    docker-compose restart
    print_success "Servicios reiniciados."
}

# Función para limpiar volúmenes y datos
clean_data() {
    read -p "⚠️  ¿Estás seguro de que quieres eliminar todos los datos? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Limpiando datos..."
        docker-compose down -v
        docker system prune -f
        print_success "Datos limpiados."
    fi
}

# Función para mostrar estado de servicios
show_status() {
    print_status "Estado de servicios:"
    docker-compose ps
}

# Función para ejecutar migraciones de base de datos
run_migrations() {
    print_status "Ejecutando migraciones de base de datos..."
    docker-compose exec backend python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
print('✅ Migraciones completadas')
"
}

# Función para mostrar URLs importantes
show_urls() {
    echo ""
    print_success "🎉 ¡Agente de IA iniciado correctamente!"
    echo ""
    echo "📍 URLs importantes:"
    echo "   • API Backend:     http://localhost:8000"
    echo "   • Documentación:   http://localhost:8000/docs"
    echo "   • Frontend:        http://localhost:3000"
    echo "   • PgAdmin:         http://localhost:5050"
    echo "   • Flower (Celery): http://localhost:5555"
    echo ""
    echo "🔑 Credenciales por defecto:"
    echo "   • PgAdmin: admin@shopify-ai.com / admin123"
    echo ""
    echo "📚 Próximos pasos:"
    echo "   1. Configura tus credenciales de Shopify en el archivo .env"
    echo "   2. Configura tu API key de OpenAI en el archivo .env"
    echo "   3. Accede a la documentación en http://localhost:8000/docs"
    echo ""
}

# Función principal de inicio
start_services() {
    print_status "Iniciando servicios con Docker Compose..."
    
    # Construir imágenes si es necesario
    docker-compose build
    
    # Iniciar servicios base
    docker-compose up -d postgres redis
    
    # Esperar a que estén listos
    wait_for_service postgres
    wait_for_service redis
    
    # Iniciar backend
    docker-compose up -d backend
    wait_for_service backend
    
    # Ejecutar migraciones
    sleep 5  # Dar tiempo al backend para inicializar completamente
    run_migrations
    
    # Iniciar resto de servicios
    docker-compose up -d
    
    # Mostrar URLs
    show_urls
}

# Función para desarrollo
start_dev() {
    print_status "Iniciando en modo desarrollo..."
    
    # Iniciar solo servicios necesarios para desarrollo
    docker-compose up -d postgres redis
    wait_for_service postgres
    wait_for_service redis
    
    print_success "Servicios base iniciados para desarrollo."
    print_status "Para iniciar el backend: cd backend && python -m uvicorn main:app --reload"
    print_status "Para iniciar el frontend: cd frontend && npm start"
}

# Función para producción
start_prod() {
    print_status "Iniciando en modo producción..."
    docker-compose --profile production up -d
    wait_for_service backend
    run_migrations
    show_urls
}

# Función de ayuda
show_help() {
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start     - Inicia todos los servicios (por defecto)"
    echo "  dev       - Inicia solo servicios base para desarrollo local"
    echo "  prod      - Inicia en modo producción"
    echo "  stop      - Detiene todos los servicios"
    echo "  restart   - Reinicia todos los servicios"
    echo "  status    - Muestra estado de servicios"
    echo "  logs      - Muestra logs en tiempo real"
    echo "  clean     - Limpia todos los datos y volúmenes"
    echo "  migrate   - Ejecuta migraciones de base de datos"
    echo "  help      - Muestra esta ayuda"
    echo ""
}

# Manejo de señales para limpieza
trap 'echo -e "\n${YELLOW}Recibida señal de interrupción...${NC}"; exit 0' INT TERM

# Procesamiento de argumentos
case "${1:-start}" in
    "start")
        start_services
        ;;
    "dev")
        start_dev
        ;;
    "prod")
        start_prod
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        clean_data
        ;;
    "migrate")
        run_migrations
        ;;
    "help")
        show_help
        ;;
    *)
        print_error "Comando desconocido: $1"
        show_help
        exit 1
        ;;
esac