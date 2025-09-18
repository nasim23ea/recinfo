"""
Modelos de Base de Datos
Define las estructuras de datos para el agente de IA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Shop(Base):
    """
    Modelo para almacenar información de tiendas Shopify
    """
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String(255), unique=True, index=True, nullable=False)
    shop_name = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)  # Encriptado en producción
    webhook_secret = Column(String(255))
    
    # Información de la tienda
    currency = Column(String(10), default="USD")
    timezone = Column(String(100))
    plan_name = Column(String(100))
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    
    # Configuración del agente de IA
    ai_settings = Column(JSON, default={})
    
    # Relaciones
    interactions = relationship("ChatInteraction", back_populates="shop")
    analytics = relationship("ShopAnalytics", back_populates="shop")
    customers = relationship("CustomerProfile", back_populates="shop")

class ChatInteraction(Base):
    """
    Modelo para almacenar interacciones con el agente de IA
    """
    __tablename__ = "chat_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)  # UUID para agrupar conversaciones
    
    # Relación con tienda
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(String(255), index=True)  # ID del cliente en Shopify
    
    # Contenido de la interacción
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    context_data = Column(JSON)  # Contexto usado para generar la respuesta
    
    # Análisis de la interacción
    intent = Column(String(100))  # Intención detectada
    confidence_score = Column(Float)
    sports_teams_mentioned = Column(JSON)  # Lista de equipos mencionados
    actions_suggested = Column(JSON)  # Acciones sugeridas por el agente
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    response_time_ms = Column(Integer)  # Tiempo de respuesta en millisegundos
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Feedback del usuario
    user_rating = Column(Integer)  # 1-5 estrellas
    user_feedback = Column(Text)
    
    # Relaciones
    shop = relationship("Shop", back_populates="interactions")

class CustomerProfile(Base):
    """
    Modelo para perfiles de clientes con preferencias deportivas
    """
    __tablename__ = "customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    shopify_customer_id = Column(String(255), nullable=False, index=True)
    
    # Información básica del cliente
    email = Column(String(255), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    location_city = Column(String(255))
    location_state = Column(String(255))
    location_country = Column(String(255))
    
    # Preferencias deportivas inferidas
    favorite_teams = Column(JSON, default=[])  # Lista de equipos favoritos
    team_preferences_confidence = Column(Float, default=0.0)  # Confianza en las preferencias
    sport_interests = Column(JSON, default=[])  # Tipos de deportes de interés
    fan_loyalty_level = Column(String(50))  # casual, moderate, fanatic
    
    # Comportamiento de compra
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    avg_order_value = Column(Float, default=0.0)
    last_order_date = Column(DateTime)
    preferred_product_categories = Column(JSON, default=[])
    
    # Análisis de temporada
    seasonal_purchase_patterns = Column(JSON, default={})
    game_day_purchase_behavior = Column(JSON, default={})
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime)
    profile_completeness = Column(Float, default=0.0)  # 0.0 - 1.0
    
    # Relaciones
    shop = relationship("Shop", back_populates="customers")

class ShopAnalytics(Base):
    """
    Modelo para almacenar analytics de la tienda relacionados con deportes
    """
    __tablename__ = "shop_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    # Período de análisis
    analysis_date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Métricas de ventas generales
    total_revenue = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0.0)
    
    # Métricas por equipos deportivos
    team_sales_breakdown = Column(JSON, default={})  # Ventas por equipo
    top_performing_teams = Column(JSON, default=[])  # Top 10 equipos por ventas
    team_correlation_scores = Column(JSON, default={})  # Correlación rendimiento-ventas
    
    # Análisis de productos deportivos
    sports_product_revenue = Column(Float, default=0.0)
    sports_product_percentage = Column(Float, default=0.0)
    top_sports_products = Column(JSON, default=[])
    
    # Insights del agente de IA
    ai_recommendations_given = Column(Integer, default=0)
    ai_recommendations_followed = Column(Integer, default=0)
    ai_success_rate = Column(Float, default=0.0)
    
    # Predicciones y tendencias
    predicted_trends = Column(JSON, default={})
    seasonal_patterns = Column(JSON, default={})
    upcoming_opportunities = Column(JSON, default=[])
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    shop = relationship("Shop", back_populates="analytics")

class SportsTeamData(Base):
    """
    Modelo para almacenar datos procesados de equipos deportivos
    """
    __tablename__ = "sports_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(255), unique=True, nullable=False, index=True)
    
    # Estadísticas actuales
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)
    
    # Estadísticas ofensivas/defensivas
    avg_points_for = Column(Float, default=0.0)
    avg_points_against = Column(Float, default=0.0)
    point_differential = Column(Float, default=0.0)
    
    # Rendimiento por ubicación
    home_wins = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    
    # Análisis avanzado
    strength_of_schedule = Column(Float, default=0.0)
    recent_form = Column(String(20))  # hot, good, average, struggling, cold
    momentum_score = Column(Float, default=0.0)
    
    # Características del equipo
    strengths = Column(JSON, default=[])
    weaknesses = Column(JSON, default=[])
    play_style = Column(String(100))
    
    # Información comercial
    fan_base_size = Column(String(20))  # small, medium, large, huge
    merchandise_popularity = Column(Float, default=0.0)
    social_media_following = Column(Integer, default=0)
    
    # Metadatos
    last_updated = Column(DateTime, default=datetime.utcnow)
    season = Column(String(20))
    conference = Column(String(100))
    division = Column(String(100))
    
    # Relaciones
    games = relationship("GameResult", foreign_keys="[GameResult.home_team_id, GameResult.away_team_id]")

class GameResult(Base):
    """
    Modelo para almacenar resultados de partidos
    """
    __tablename__ = "game_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Equipos participantes
    home_team_id = Column(Integer, ForeignKey("sports_teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("sports_teams.id"), nullable=False)
    
    # Resultado del partido
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    winner_id = Column(Integer, ForeignKey("sports_teams.id"))
    
    # Detalles del partido
    game_date = Column(DateTime, index=True)
    week_number = Column(Integer)
    season = Column(String(20))
    game_type = Column(String(50))  # regular, playoff, championship
    
    # Análisis del partido
    margin_of_victory = Column(Integer)
    total_points = Column(Integer)
    is_upset = Column(Boolean, default=False)
    is_close_game = Column(Boolean, default=False)  # <= 7 points
    is_blowout = Column(Boolean, default=False)  # >= 21 points
    
    # Impacto comercial
    pre_game_buzz = Column(Float, default=0.0)  # Expectativa antes del juego
    post_game_sales_impact = Column(Float, default=0.0)  # Impacto en ventas después
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    data_source = Column(String(100))  # manual, api, scraping
    
    # Relaciones
    home_team = relationship("SportsTeamData", foreign_keys=[home_team_id])
    away_team = relationship("SportsTeamData", foreign_keys=[away_team_id])
    winner = relationship("SportsTeamData", foreign_keys=[winner_id])

class AIAgentSession(Base):
    """
    Modelo para sesiones del agente de IA con contexto persistente
    """
    __tablename__ = "ai_agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Información de la sesión
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(String(255), index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    
    # Contexto acumulado
    conversation_history = Column(JSON, default=[])
    inferred_preferences = Column(JSON, default={})
    mentioned_teams = Column(JSON, default=[])
    product_interests = Column(JSON, default=[])
    
    # Estado de la sesión
    current_intent = Column(String(100))
    conversation_stage = Column(String(50))  # greeting, inquiry, recommendation, purchase
    satisfaction_score = Column(Float)
    
    # Métricas de rendimiento
    total_interactions = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    successful_recommendations = Column(Integer, default=0)
    
    # Metadatos
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

class ProductRecommendation(Base):
    """
    Modelo para almacenar recomendaciones de productos generadas por IA
    """
    __tablename__ = "product_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información de la recomendación
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(String(255), index=True)
    session_id = Column(String(255), index=True)
    
    # Producto recomendado
    shopify_product_id = Column(String(255), nullable=False)
    product_title = Column(String(500))
    product_price = Column(Float)
    product_tags = Column(JSON, default=[])
    
    # Contexto de la recomendación
    recommendation_reason = Column(Text)
    related_teams = Column(JSON, default=[])
    confidence_score = Column(Float)
    recommendation_type = Column(String(50))  # trending, personalized, seasonal, etc.
    
    # Factores de recomendación
    team_performance_factor = Column(Float, default=0.0)
    customer_history_factor = Column(Float, default=0.0)
    seasonal_factor = Column(Float, default=0.0)
    popularity_factor = Column(Float, default=0.0)
    
    # Resultados
    was_viewed = Column(Boolean, default=False)
    was_clicked = Column(Boolean, default=False)
    was_purchased = Column(Boolean, default=False)
    time_to_action = Column(Integer)  # Segundos hasta la acción
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    viewed_at = Column(DateTime)
    clicked_at = Column(DateTime)
    purchased_at = Column(DateTime)

class MarketingInsight(Base):
    """
    Modelo para insights de marketing generados por el agente de IA
    """
    __tablename__ = "marketing_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    # Tipo de insight
    insight_type = Column(String(100), nullable=False)  # trend, opportunity, warning, etc.
    category = Column(String(100))  # team_performance, seasonal, customer_behavior
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Contenido del insight
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendations = Column(JSON, default=[])
    
    # Datos de soporte
    supporting_data = Column(JSON, default={})
    confidence_level = Column(Float, default=0.0)
    potential_impact = Column(String(20))  # low, medium, high
    
    # Relacionado con equipos deportivos
    related_teams = Column(JSON, default=[])
    related_products = Column(JSON, default=[])
    seasonal_relevance = Column(String(50))
    
    # Estado del insight
    status = Column(String(50), default="new")  # new, reviewed, actioned, dismissed
    acted_upon = Column(Boolean, default=False)
    action_taken = Column(Text)
    results = Column(JSON, default={})
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # Algunos insights son temporales
    reviewed_at = Column(DateTime)
    actioned_at = Column(DateTime)

# Funciones auxiliares para trabajar con los modelos

def create_session_id() -> str:
    """Genera un ID único para sesiones"""
    return str(uuid.uuid4())

def calculate_profile_completeness(customer: CustomerProfile) -> float:
    """Calcula qué tan completo está un perfil de cliente"""
    total_fields = 10
    completed_fields = 0
    
    if customer.email:
        completed_fields += 1
    if customer.first_name and customer.last_name:
        completed_fields += 1
    if customer.location_city and customer.location_state:
        completed_fields += 1
    if customer.favorite_teams:
        completed_fields += 1
    if customer.sport_interests:
        completed_fields += 1
    if customer.total_orders > 0:
        completed_fields += 1
    if customer.preferred_product_categories:
        completed_fields += 1
    if customer.seasonal_purchase_patterns:
        completed_fields += 1
    if customer.fan_loyalty_level:
        completed_fields += 1
    if customer.team_preferences_confidence > 0.5:
        completed_fields += 1
    
    return completed_fields / total_fields

def get_trending_teams(session, days: int = 7) -> list:
    """Obtiene equipos con tendencia ascendente basado en interacciones recientes"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Contar menciones de equipos en interacciones recientes
    mentions = session.query(
        ChatInteraction.sports_teams_mentioned
    ).filter(
        ChatInteraction.created_at >= cutoff_date
    ).all()
    
    team_counts = {}
    for mention in mentions:
        if mention.sports_teams_mentioned:
            for team in mention.sports_teams_mentioned:
                team_counts[team] = team_counts.get(team, 0) + 1
    
    # Ordenar por frecuencia de mención
    return sorted(team_counts.items(), key=lambda x: x[1], reverse=True)[:10]