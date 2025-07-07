# 🚀 Guía de Instalación - Agente de IA para Shopify

Esta guía te llevará paso a paso para configurar y ejecutar tu agente de IA para Shopify que integra datos deportivos con información de la tienda.

## 📋 Prerrequisitos

### Software Requerido

1. **Docker** (v20.10+)
   - [Instalar Docker](https://docs.docker.com/get-docker/)
   - [Instalar Docker Compose](https://docs.docker.com/compose/install/)

2. **Git**
   - [Instalar Git](https://git-scm.com/downloads)

3. **Cuentas y APIs Necesarias**
   - Cuenta de Shopify Partners
   - API Key de OpenAI
   - Tienda de desarrollo de Shopify

### Credenciales Necesarias

Antes de comenzar, asegúrate de tener:
- **Shopify API Key** y **API Secret**
- **OpenAI API Key**
- **Token de acceso** de tu tienda de Shopify

## 🏗️ Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/shopify-ai-agent.git
cd shopify-ai-agent
```

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env  # o usar tu editor preferido
```

### 3. Configurar Credenciales Mínimas

Edita el archivo `.env` con al menos estas variables:

```env
# Shopify
SHOPIFY_API_KEY=tu_api_key_aqui
SHOPIFY_API_SECRET=tu_api_secret_aqui
SHOPIFY_WEBHOOK_SECRET=tu_webhook_secret

# OpenAI
OPENAI_API_KEY=sk-proj-tu_openai_key_aqui

# Base de datos
DATABASE_URL=postgresql://postgres:password@localhost:5432/shopify_ai_agent
```

### 4. Iniciar la Aplicación

```bash
# Hacer el script ejecutable
chmod +x scripts/start.sh

# Iniciar todos los servicios
./scripts/start.sh
```

¡Listo! Tu agente de IA estará disponible en:
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## 📝 Configuración Detallada

### Configuración de Shopify

1. **Crear App de Shopify**:
   - Ve a [Shopify Partners](https://partners.shopify.com/)
   - Crea una nueva app
   - Anota API Key y API Secret

2. **Configurar Permisos**:
   ```
   - read_products
   - write_products
   - read_orders
   - read_customers
   - write_customers
   ```

3. **Configurar Webhooks**:
   - URL: `https://tu-dominio.com/webhooks/shopify/orders/create`
   - Events: Order creation, Customer creation

### Configuración de OpenAI

1. **Obtener API Key**:
   - Ve a [OpenAI Platform](https://platform.openai.com/)
   - Crea una API Key
   - Configura límites de uso

2. **Modelos Recomendados**:
   - **Producción**: `gpt-4`
   - **Desarrollo**: `gpt-3.5-turbo`

### Datos Deportivos

Los archivos `equipos.txt` y `partidos.txt` contienen datos de ejemplo. Para usar tus propios datos:

1. **Formato de Equipos** (`equipos.txt`):
   ```
   Alabama,Georgia,Florida,Auburn,LSU,Tennessee...
   ```

2. **Formato de Partidos** (`partidos.txt`):
   ```
   Alabama,52,vs,Southern California,6
   Georgia,33,at,Missouri,27
   ```

## 🔧 Comandos Útiles

### Gestión de Servicios

```bash
# Iniciar en modo desarrollo
./scripts/start.sh dev

# Iniciar en producción
./scripts/start.sh prod

# Ver estado de servicios
./scripts/start.sh status

# Ver logs en tiempo real
./scripts/start.sh logs

# Detener servicios
./scripts/start.sh stop

# Reiniciar servicios
./scripts/start.sh restart

# Limpiar datos
./scripts/start.sh clean
```

### Desarrollo Local

Si prefieres desarrollar sin Docker:

```bash
# Iniciar solo servicios base
./scripts/start.sh dev

# En otra terminal - Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# En otra terminal - Frontend
cd frontend
npm install
npm start
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de Conexión a Base de Datos**
   ```bash
   # Verificar que PostgreSQL esté ejecutándose
   docker-compose ps postgres
   
   # Reiniciar base de datos
   docker-compose restart postgres
   ```

2. **Error de API de OpenAI**
   ```bash
   # Verificar API key en .env
   grep OPENAI_API_KEY .env
   
   # Verificar límites en OpenAI Platform
   ```

3. **Error de Permisos de Shopify**
   ```bash
   # Verificar scopes en shopify.app.toml
   # Reinstalar app en la tienda
   ```

### Logs y Debugging

```bash
# Ver logs del backend
docker-compose logs backend

# Ver logs de la base de datos
docker-compose logs postgres

# Ver todos los logs
docker-compose logs

# Entrar al contenedor backend
docker-compose exec backend bash
```

## 🏥 Verificación de Salud

### Endpoints de Salud

- **API Status**: `GET http://localhost:8000/`
- **Database Health**: `GET http://localhost:8000/health`
- **Sports Data**: `GET http://localhost:8000/teams`

### Verificar Integración

1. **Test de Chat**:
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "¿Cómo está jugando Alabama esta temporada?"}'
   ```

2. **Test de Recomendaciones**:
   ```bash
   curl -X POST http://localhost:8000/recommendations/products \
     -H "Content-Type: application/json" \
     -d '{"team_name": "Alabama"}'
   ```

## 🚀 Despliegue en Producción

### Variables de Entorno de Producción

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/db
REDIS_URL=redis://prod-redis:6379/0
SECRET_KEY=your-super-secure-secret-key
ENABLE_SENTRY=true
SENTRY_DSN=your-sentry-dsn
```

### Usando Railway / Heroku

1. **Railway**:
   ```bash
   # Instalar Railway CLI
   npm install -g @railway/cli
   
   # Login y deploy
   railway login
   railway link
   railway up
   ```

2. **Heroku**:
   ```bash
   # Instalar Heroku CLI
   # Crear app
   heroku create your-app-name
   
   # Configurar variables
   heroku config:set OPENAI_API_KEY=your-key
   
   # Deploy
   git push heroku main
   ```

### Usando Docker en VPS

```bash
# En tu servidor
git clone https://github.com/tu-usuario/shopify-ai-agent.git
cd shopify-ai-agent

# Configurar producción
cp .env.example .env
# Editar .env con configuración de producción

# Iniciar
./scripts/start.sh prod
```

## 📊 Monitoreo y Analytics

### Servicios Incluidos

- **PgAdmin**: http://localhost:5050 (admin@shopify-ai.com / admin123)
- **Flower (Celery)**: http://localhost:5555
- **Prometheus**: http://localhost:9090 (con profile monitoring)
- **Grafana**: http://localhost:3001 (admin / admin123)

### Métricas Importantes

- Tiempo de respuesta del agente
- Precisión de recomendaciones
- Correlación ventas-deportes
- Satisfacción del cliente

## 🔐 Seguridad

### Mejores Prácticas

1. **Variables de Entorno**:
   - Nunca commits `.env` al repositorio
   - Usa secretos específicos por entorno

2. **API Keys**:
   - Rotar keys regularmente
   - Configurar límites de uso

3. **Base de Datos**:
   - Usar SSL en producción
   - Configurar backups automáticos

4. **Webhooks**:
   - Verificar siempre la autenticidad
   - Usar HTTPS en producción

## 📞 Soporte

### Recursos Útiles

- **Documentación de Shopify**: [shopify.dev](https://shopify.dev)
- **OpenAI API Docs**: [platform.openai.com](https://platform.openai.com/docs)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

### Reportar Problemas

Si encuentras problemas:

1. Revisa esta guía primero
2. Verifica los logs: `./scripts/start.sh logs`
3. Busca en issues existentes
4. Crea un nuevo issue con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Información del entorno

## 🎉 ¡Siguiente Paso!

Una vez que tengas todo funcionando:

1. **Personaliza tu agente** editando prompts en `backend/ai_agent.py`
2. **Añade más datos deportivos** actualizando los archivos .txt
3. **Configura webhooks** en tu tienda de Shopify
4. **Implementa analytics** personalizados
5. **Despliega en producción**

¡Disfruta tu nuevo agente de IA para Shopify! 🚀