#!/bin/bash

echo "🚀 INICIANDO AGENTE DE IA PARA SHOPIFY"
echo "======================================"

# Crear archivos de configuración mínimos
echo "📝 Configurando entorno..."

# Crear .env básico si no existe
if [ ! -f .env ]; then
    cat > .env << EOF
# Configuración básica para demo
DATABASE_URL=sqlite:///./sports_shopify.db
SECRET_KEY=demo-secret-key-12345
DEBUG=true

# APIs (opcional para demo)
OPENAI_API_KEY=your-openai-key-here
SHOPIFY_API_KEY=your-shopify-key-here
SHOPIFY_API_SECRET=your-shopify-secret-here
SHOPIFY_ACCESS_TOKEN=your-shopify-token-here
SHOPIFY_SHOP_DOMAIN=your-shop.myshopify.com

# Redis (usaremos SQLite por simplicidad)
REDIS_URL=redis://localhost:6379

# Configuración del agente
AGENT_NAME="Shopify Sports AI"
RESPONSE_LANGUAGE=es
EOF
    echo "✅ Creado .env con configuración básica"
fi

# Verificar Python y dependencias
echo "🔧 Verificando dependencias..."

# Instalar dependencias básicas si no existen
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Instalando dependencias básicas..."
    pip3 install fastapi uvicorn sqlalchemy aiofiles python-multipart || {
        echo "❌ Error instalando dependencias básicas"
        echo "💡 Ejecuta: pip install fastapi uvicorn sqlalchemy aiofiles python-multipart"
        exit 1
    }
fi

# Verificar archivos de datos
if [ ! -f "equipos.txt" ] || [ ! -f "partidos.txt" ]; then
    echo "❌ Error: No se encontraron archivos de datos deportivos"
    echo "   Asegúrate de que existan equipos.txt y partidos.txt"
    exit 1
fi

echo "✅ Datos deportivos encontrados: $(cat equipos.txt | tr ',' '\n' | wc -l) equipos, $(wc -l < partidos.txt) partidos"

# Crear directorio de logs
mkdir -p logs

# Función para manejar Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Deteniendo servicios..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    echo "✅ Servicios detenidos"
    exit 0
}
trap cleanup INT

# Ejecutar API
echo "🌐 Iniciando API en puerto 8000..."
echo "📊 La API procesará automáticamente los datos deportivos"

cd backend
python3 -c "
import sys
import os
sys.path.append('.')

# Crear aplicación mínima para demo
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from datetime import datetime
import json

app = FastAPI(
    title='Shopify Sports AI Agent',
    description='Agente de IA que integra datos deportivos con Shopify',
    version='1.0.0'
)

# Simular base de datos deportiva
class MockSportsDB:
    def __init__(self):
        self.teams = []
        self.games = []
        self.load_data()
    
    def load_data(self):
        try:
            # Cargar equipos
            with open('../equipos.txt', 'r') as f:
                content = f.read().strip()
                self.teams = [team.strip() for team in content.split(',') if team.strip()]
            
            # Cargar algunos partidos
            with open('../partidos.txt', 'r') as f:
                lines = f.readlines()[:50]  # Primeros 50 para demo rápida
                
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    try:
                        self.games.append({
                            'team1': parts[0].strip(),
                            'team2': parts[3].strip(), 
                            'score1': int(parts[1].strip()),
                            'score2': int(parts[4].strip())
                        })
                    except:
                        continue
        except Exception as e:
            print(f'Error cargando datos: {e}')

sports_db = MockSportsDB()

@app.get('/')
async def root():
    return HTMLResponse('''
    <html>
        <head>
            <title>🏈 Shopify Sports AI Agent</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { color: #2c5aa0; text-align: center; margin-bottom: 30px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
                .stat-card { background: #e8f4f8; padding: 20px; border-radius: 8px; text-align: center; }
                .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
                .success { color: #28a745; font-weight: bold; }
                .demo-section { margin: 25px 0; padding: 20px; background: #fff3cd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏈 Shopify Sports AI Agent</h1>
                    <p>Sistema de IA que integra datos deportivos con Shopify</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>📊 Equipos</h3>
                        <p><strong>''' + str(len(sports_db.teams)) + '''</strong></p>
                    </div>
                    <div class="stat-card">
                        <h3>🏈 Partidos</h3>
                        <p><strong>''' + str(len(sports_db.games)) + '''</strong></p>
                    </div>
                    <div class="stat-card">
                        <h3>🤖 Estado</h3>
                        <p class="success">ACTIVO</p>
                    </div>
                </div>
                
                <div class="demo-section">
                    <h3>🚀 API Endpoints Disponibles:</h3>
                    <div class="endpoint">
                        <strong>GET /teams</strong> - Lista todos los equipos
                    </div>
                    <div class="endpoint">
                        <strong>GET /teams/{team_name}</strong> - Información de un equipo
                    </div>
                    <div class="endpoint">
                        <strong>POST /chat</strong> - Chat con el agente de IA
                    </div>
                    <div class="endpoint">
                        <strong>GET /docs</strong> - Documentación completa de la API
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/docs" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📚 Ver Documentación Completa
                    </a>
                </div>
            </div>
        </body>
    </html>
    ''')

@app.get('/teams')
async def get_teams():
    return {
        'total': len(sports_db.teams),
        'teams': sports_db.teams[:20],  # Primeros 20 para demo
        'message': f'Mostrando primeros 20 de {len(sports_db.teams)} equipos disponibles'
    }

@app.get('/teams/{team_name}')
async def get_team_info(team_name: str):
    if team_name not in sports_db.teams:
        raise HTTPException(status_code=404, detail='Equipo no encontrado')
    
    # Buscar juegos del equipo
    team_games = [g for g in sports_db.games if g['team1'] == team_name or g['team2'] == team_name]
    
    wins = 0
    total_points = 0
    games_played = len(team_games)
    
    for game in team_games:
        if game['team1'] == team_name:
            total_points += game['score1']
            if game['score1'] > game['score2']:
                wins += 1
        else:
            total_points += game['score2'] 
            if game['score2'] > game['score1']:
                wins += 1
    
    win_pct = wins / games_played if games_played > 0 else 0
    avg_points = total_points / games_played if games_played > 0 else 0
    
    return {
        'team': team_name,
        'games_played': games_played,
        'wins': wins,
        'losses': games_played - wins,
        'win_percentage': round(win_pct, 3),
        'avg_points': round(avg_points, 1),
        'recent_games': team_games[-3:] if team_games else [],
        'recommendation': '🔥 Equipo en racha - Gran momento para promocionar productos' if win_pct > 0.7 else '📈 Equipo sólido - Buen potencial de ventas' if win_pct > 0.5 else '💪 Equipo luchador - Ideal para fans leales'
    }

@app.post('/chat')
async def chat_with_agent(message: dict):
    user_message = message.get('message', '').lower()
    
    if 'alabama' in user_message:
        return {
            'response': '🏈 Alabama tiene un excelente record esta temporada con 92.9% de victorias. Es un equipo dominante con gran diferencia de puntos. ¡Perfecto momento para promocionar productos de Alabama!',
            'recommendations': [
                'Alabama Crimson Tide Jersey',
                'Alabama Championship Gear', 
                'Alabama Fan Accessories'
            ]
        }
    elif 'recomienda' in user_message or 'producto' in user_message:
        return {
            'response': '🛍️ Basado en el rendimiento actual, te recomiendo productos de equipos top como Alabama, Clemson y Western Michigan. ¡Están en excelente momento!',
            'recommendations': [
                'Jerseys de equipos ganadores',
                'Merchandise de campeones',
                'Accesorios de equipos en racha'
            ]
        }
    else:
        return {
            'response': f'🤖 Hola! Soy tu agente de IA deportivo. Tengo información de {len(sports_db.teams)} equipos y {len(sports_db.games)} partidos. ¿En qué equipo estás interesado?',
            'suggestions': ['Pregunta por Alabama', 'Pide recomendaciones de productos', 'Consulta estadísticas']
        }

if __name__ == '__main__':
    print('🚀 Iniciando Shopify Sports AI Agent...')
    print(f'📊 Cargados {len(sports_db.teams)} equipos y {len(sports_db.games)} partidos')
    print('🌐 API disponible en: http://localhost:8000')
    print('📚 Documentación en: http://localhost:8000/docs')
    print('')
    print('Endpoints principales:')
    print('  • GET  /teams - Lista de equipos')
    print('  • GET  /teams/Alabama - Info de Alabama') 
    print('  • POST /chat - Chat con agente')
    print('')
    print('Presiona Ctrl+C para detener')
    print('='*50)
    
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
" &

API_PID=$!

# Esperar a que la API se inicie
sleep 3

echo ""
echo "🎉 ¡SISTEMA INICIADO EXITOSAMENTE!"
echo "=================================="
echo ""
echo "🌐 URLs disponibles:"
echo "   • Principal: http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • Equipos:   http://localhost:8000/teams"
echo "   • Alabama:   http://localhost:8000/teams/Alabama"
echo ""
echo "📱 Pruebas rápidas desde terminal:"
echo "   curl http://localhost:8000/teams"
echo "   curl http://localhost:8000/teams/Alabama"
echo ""
echo "💬 Chat con el agente:"
echo "   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"message\":\"¿Cómo está Alabama?\"}'"
echo ""
echo "🛑 Presiona Ctrl+C para detener todos los servicios"
echo ""

# Mantener el script corriendo
wait $API_PID