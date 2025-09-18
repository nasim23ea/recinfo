"""
Agente de IA para Shopify - Backend Principal
Integra datos de Shopify con base de datos deportiva privada
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import asyncio
from datetime import datetime
import logging

# Importaciones locales
from .database import get_db, init_db
from .shopify_client import ShopifyClient
from .ai_agent import AIAgent
from .sports_data import SportsDatabase
from .models import *

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de FastAPI
app = FastAPI(
    title="Shopify AI Agent",
    description="Agente de IA que integra datos de Shopify con información deportiva",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticación
security = HTTPBearer()

# Instancias globales
shopify_client = ShopifyClient()
ai_agent = AIAgent()
sports_db = SportsDatabase()

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la aplicación"""
    try:
        await init_db()
        await sports_db.load_data()
        logger.info("✅ Aplicación iniciada correctamente")
    except Exception as e:
        logger.error(f"❌ Error al iniciar aplicación: {e}")
        raise

# Modelos de datos
class ChatMessage(BaseModel):
    message: str
    shop_domain: Optional[str] = None
    customer_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ProductRecommendationRequest(BaseModel):
    team_name: Optional[str] = None
    customer_preferences: Optional[List[str]] = None
    recent_games: Optional[bool] = True
    budget_range: Optional[tuple] = None

class AnalyticsRequest(BaseModel):
    team_name: str
    date_range: Optional[tuple] = None
    metrics: List[str] = ["sales", "engagement", "inventory"]

# Middleware de autenticación
async def verify_shopify_webhook(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica la autenticidad de webhooks de Shopify"""
    # Implementar verificación de webhook de Shopify
    return credentials.credentials

# ENDPOINTS PRINCIPALES

@app.get("/")
async def root():
    """Endpoint de salud de la aplicación"""
    return {
        "message": "🤖 Shopify AI Agent v1.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "product_recommendations", 
            "sales_analytics", 
            "customer_support",
            "sports_data_integration"
        ]
    }

@app.post("/chat")
async def chat_with_agent(message: ChatMessage, db = Depends(get_db)):
    """
    Endpoint principal para interactuar con el agente de IA
    """
    try:
        # Obtener contexto de Shopify si se proporciona
        shopify_context = {}
        if message.shop_domain:
            shopify_context = await shopify_client.get_shop_context(message.shop_domain)
        
        # Obtener datos deportivos relevantes
        sports_context = await sports_db.get_relevant_context(message.message)
        
        # Procesar con el agente de IA
        response = await ai_agent.process_message(
            message=message.message,
            shopify_context=shopify_context,
            sports_context=sports_context,
            customer_id=message.customer_id,
            additional_context=message.context
        )
        
        # Guardar interacción en base de datos
        await save_interaction(db, message, response)
        
        return {
            "response": response["text"],
            "actions": response.get("actions", []),
            "recommendations": response.get("recommendations", []),
            "confidence": response.get("confidence", 0.8),
            "sports_insights": response.get("sports_insights", {})
        }
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations/products")
async def get_product_recommendations(request: ProductRecommendationRequest, db = Depends(get_db)):
    """
    Genera recomendaciones de productos basadas en datos deportivos
    """
    try:
        # Obtener información del equipo
        team_info = None
        if request.team_name:
            team_info = await sports_db.get_team_info(request.team_name)
        
        # Obtener productos relevantes de Shopify
        products = await shopify_client.get_products_by_criteria(
            team_name=request.team_name,
            budget_range=request.budget_range
        )
        
        # Generar recomendaciones con IA
        recommendations = await ai_agent.generate_product_recommendations(
            team_info=team_info,
            available_products=products,
            customer_preferences=request.customer_preferences,
            include_recent_performance=request.recent_games
        )
        
        return {
            "recommendations": recommendations,
            "team_performance": team_info.get("recent_performance", {}) if team_info else {},
            "total_products": len(products),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/sales/{team_name}")
async def get_sales_analytics(team_name: str, days: int = 30, db = Depends(get_db)):
    """
    Analiza ventas correlacionadas con rendimiento deportivo
    """
    try:
        # Obtener datos de ventas de Shopify
        sales_data = await shopify_client.get_sales_data(
            team_filter=team_name,
            days=days
        )
        
        # Obtener resultados deportivos
        team_results = await sports_db.get_team_results(
            team_name=team_name,
            days=days
        )
        
        # Análisis con IA
        analysis = await ai_agent.analyze_sales_correlation(
            sales_data=sales_data,
            team_performance=team_results
        )
        
        return {
            "team": team_name,
            "period_days": days,
            "total_sales": sales_data.get("total", 0),
            "correlation_analysis": analysis,
            "performance_impact": analysis.get("performance_impact", {}),
            "recommendations": analysis.get("recommendations", [])
        }
        
    except Exception as e:
        logger.error(f"Error en analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams")
async def get_teams():
    """Obtiene lista de equipos disponibles"""
    try:
        teams = await sports_db.get_all_teams()
        return {
            "teams": teams,
            "total": len(teams),
            "last_updated": await sports_db.get_last_update()
        }
    except Exception as e:
        logger.error(f"Error obteniendo equipos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_name}/performance")
async def get_team_performance(team_name: str, season: str = "current"):
    """Obtiene rendimiento detallado de un equipo"""
    try:
        performance = await sports_db.get_detailed_performance(team_name, season)
        return performance
    except Exception as e:
        logger.error(f"Error obteniendo rendimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WEBHOOKS DE SHOPIFY

@app.post("/webhooks/shopify/orders/create")
async def handle_new_order(
    order_data: dict, 
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_shopify_webhook)
):
    """Maneja nuevos pedidos de Shopify"""
    try:
        # Procesar pedido en background
        background_tasks.add_task(process_new_order, order_data)
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error procesando pedido: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/shopify/customers/create")
async def handle_new_customer(
    customer_data: dict,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_shopify_webhook)
):
    """Maneja nuevos clientes de Shopify"""
    try:
        background_tasks.add_task(analyze_new_customer, customer_data)
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error procesando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TAREAS EN BACKGROUND

async def process_new_order(order_data: dict):
    """Procesa un nuevo pedido en background"""
    try:
        # Analizar productos del pedido
        team_analysis = await ai_agent.analyze_order_team_preferences(order_data)
        
        # Actualizar perfil del cliente
        if order_data.get("customer"):
            await update_customer_sports_profile(
                order_data["customer"]["id"],
                team_analysis
            )
        
        # Generar insights para marketing
        await generate_marketing_insights(order_data, team_analysis)
        
    except Exception as e:
        logger.error(f"Error procesando pedido en background: {e}")

async def analyze_new_customer(customer_data: dict):
    """Analiza un nuevo cliente para determinar preferencias deportivas"""
    try:
        # Análisis de preferencias basado en datos disponibles
        preferences = await ai_agent.infer_sports_preferences(customer_data)
        
        # Guardar en perfil del cliente
        await save_customer_preferences(customer_data["id"], preferences)
        
    except Exception as e:
        logger.error(f"Error analizando cliente: {e}")

# UTILIDADES

async def save_interaction(db, message: ChatMessage, response: dict):
    """Guarda interacción en la base de datos"""
    # Implementar guardado de interacciones para análisis
    pass

async def update_customer_sports_profile(customer_id: str, team_analysis: dict):
    """Actualiza perfil deportivo del cliente"""
    # Implementar actualización de perfil
    pass

async def generate_marketing_insights(order_data: dict, team_analysis: dict):
    """Genera insights de marketing basados en el pedido"""
    # Implementar generación de insights
    pass

async def save_customer_preferences(customer_id: str, preferences: dict):
    """Guarda preferencias deportivas del cliente"""
    # Implementar guardado de preferencias
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )