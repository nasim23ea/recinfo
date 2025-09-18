"""
Configuración de Base de Datos
Maneja conexiones y sesiones de base de datos
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator
from .models import Base

logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/shopify_ai_agent"
)

# Para desarrollo local, permitir SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False  # Cambiar a True para debug SQL
    )
else:
    # PostgreSQL en producción
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=0,
        echo=False  # Cambiar a True para debug SQL
    )

# Configurar eventos de conexión para optimizaciones
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Optimizaciones para SQLite"""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        # Habilitar foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimizaciones de rendimiento
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()

# Crear el sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def init_db():
    """
    Inicializa la base de datos creando todas las tablas
    """
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base de datos inicializada correctamente")
        
        # Verificar conexión
        with SessionLocal() as session:
            session.execute("SELECT 1")
            logger.info("✅ Conexión a base de datos verificada")
            
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise

def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesiones de base de datos para FastAPI dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    """
    Manager para operaciones avanzadas de base de datos
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_session(self) -> Session:
        """Crea una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    async def health_check(self) -> dict:
        """Verifica el estado de salud de la base de datos"""
        try:
            with self.SessionLocal() as session:
                result = session.execute("SELECT 1").scalar()
                return {
                    "status": "healthy",
                    "database": "connected",
                    "test_query": result == 1
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
    
    async def get_stats(self) -> dict:
        """Obtiene estadísticas de la base de datos"""
        try:
            with self.SessionLocal() as session:
                from .models import (
                    Shop, ChatInteraction, CustomerProfile, 
                    SportsTeamData, GameResult, ProductRecommendation
                )
                
                stats = {
                    "shops": session.query(Shop).count(),
                    "interactions": session.query(ChatInteraction).count(),
                    "customers": session.query(CustomerProfile).count(),
                    "sports_teams": session.query(SportsTeamData).count(),
                    "game_results": session.query(GameResult).count(),
                    "recommendations": session.query(ProductRecommendation).count()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error obtaining database stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, days: int = 90):
        """Limpia datos antiguos para mantener el rendimiento"""
        try:
            from datetime import datetime, timedelta
            from .models import ChatInteraction, AIAgentSession
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.SessionLocal() as session:
                # Limpiar interacciones antiguas
                old_interactions = session.query(ChatInteraction).filter(
                    ChatInteraction.created_at < cutoff_date
                ).count()
                
                session.query(ChatInteraction).filter(
                    ChatInteraction.created_at < cutoff_date
                ).delete()
                
                # Limpiar sesiones inactivas antiguas
                old_sessions = session.query(AIAgentSession).filter(
                    AIAgentSession.last_activity < cutoff_date,
                    AIAgentSession.is_active == False
                ).count()
                
                session.query(AIAgentSession).filter(
                    AIAgentSession.last_activity < cutoff_date,
                    AIAgentSession.is_active == False
                ).delete()
                
                session.commit()
                
                logger.info(f"Cleaned up {old_interactions} old interactions and {old_sessions} old sessions")
                
                return {
                    "interactions_cleaned": old_interactions,
                    "sessions_cleaned": old_sessions
                }
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    async def optimize_database(self):
        """Optimiza la base de datos"""
        try:
            with self.SessionLocal() as session:
                if DATABASE_URL.startswith("sqlite"):
                    # Optimizaciones específicas para SQLite
                    session.execute("VACUUM")
                    session.execute("ANALYZE")
                    logger.info("SQLite database optimized")
                else:
                    # Optimizaciones para PostgreSQL
                    session.execute("VACUUM ANALYZE")
                    logger.info("PostgreSQL database optimized")
                
                session.commit()
                return {"status": "optimized"}
                
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return {"error": str(e)}

# Instancia global del manager
db_manager = DatabaseManager()

# Funciones de utilidad para trabajar con datos

async def get_or_create_shop(db: Session, shop_domain: str, shop_data: dict):
    """
    Obtiene una tienda existente o crea una nueva
    """
    from .models import Shop
    
    shop = db.query(Shop).filter(Shop.shop_domain == shop_domain).first()
    
    if not shop:
        shop = Shop(
            shop_domain=shop_domain,
            shop_name=shop_data.get("name", shop_domain),
            access_token=shop_data.get("access_token", ""),
            currency=shop_data.get("currency", "USD"),
            timezone=shop_data.get("timezone"),
            plan_name=shop_data.get("plan_name")
        )
        db.add(shop)
        db.commit()
        db.refresh(shop)
        logger.info(f"Created new shop: {shop_domain}")
    
    return shop

async def save_chat_interaction(
    db: Session,
    shop_id: int,
    user_message: str,
    ai_response: str,
    context_data: dict,
    session_id: str = None,
    customer_id: str = None,
    response_time_ms: int = None
):
    """
    Guarda una interacción de chat en la base de datos
    """
    from .models import ChatInteraction, create_session_id
    
    if not session_id:
        session_id = create_session_id()
    
    interaction = ChatInteraction(
        shop_id=shop_id,
        customer_id=customer_id,
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        context_data=context_data,
        response_time_ms=response_time_ms
    )
    
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    return interaction

async def update_customer_profile(
    db: Session,
    shop_id: int,
    shopify_customer_id: str,
    profile_data: dict
):
    """
    Actualiza o crea un perfil de cliente
    """
    from .models import CustomerProfile, calculate_profile_completeness
    
    profile = db.query(CustomerProfile).filter(
        CustomerProfile.shop_id == shop_id,
        CustomerProfile.shopify_customer_id == shopify_customer_id
    ).first()
    
    if not profile:
        profile = CustomerProfile(
            shop_id=shop_id,
            shopify_customer_id=shopify_customer_id
        )
        db.add(profile)
    
    # Actualizar campos
    for field, value in profile_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)
    
    # Calcular completeness
    profile.profile_completeness = calculate_profile_completeness(profile)
    
    db.commit()
    db.refresh(profile)
    
    return profile

async def save_product_recommendation(
    db: Session,
    shop_id: int,
    customer_id: str,
    session_id: str,
    product_data: dict,
    recommendation_context: dict
):
    """
    Guarda una recomendación de producto
    """
    from .models import ProductRecommendation
    
    recommendation = ProductRecommendation(
        shop_id=shop_id,
        customer_id=customer_id,
        session_id=session_id,
        shopify_product_id=product_data.get("id"),
        product_title=product_data.get("title"),
        product_price=product_data.get("price"),
        product_tags=product_data.get("tags", []),
        recommendation_reason=recommendation_context.get("reason"),
        related_teams=recommendation_context.get("related_teams", []),
        confidence_score=recommendation_context.get("confidence", 0.0),
        recommendation_type=recommendation_context.get("type", "general"),
        team_performance_factor=recommendation_context.get("team_performance_factor", 0.0),
        customer_history_factor=recommendation_context.get("customer_history_factor", 0.0),
        seasonal_factor=recommendation_context.get("seasonal_factor", 0.0),
        popularity_factor=recommendation_context.get("popularity_factor", 0.0)
    )
    
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    
    return recommendation

async def create_marketing_insight(
    db: Session,
    shop_id: int,
    insight_data: dict
):
    """
    Crea un nuevo insight de marketing
    """
    from .models import MarketingInsight
    
    insight = MarketingInsight(
        shop_id=shop_id,
        insight_type=insight_data.get("type"),
        category=insight_data.get("category"),
        priority=insight_data.get("priority", "medium"),
        title=insight_data.get("title"),
        description=insight_data.get("description"),
        recommendations=insight_data.get("recommendations", []),
        supporting_data=insight_data.get("supporting_data", {}),
        confidence_level=insight_data.get("confidence", 0.0),
        potential_impact=insight_data.get("impact", "medium"),
        related_teams=insight_data.get("related_teams", []),
        related_products=insight_data.get("related_products", []),
        seasonal_relevance=insight_data.get("seasonal_relevance"),
        expires_at=insight_data.get("expires_at")
    )
    
    db.add(insight)
    db.commit()
    db.refresh(insight)
    
    return insight

async def get_customer_analytics(db: Session, shop_id: int, days: int = 30):
    """
    Obtiene analytics de clientes para una tienda
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from .models import CustomerProfile, ChatInteraction
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Estadísticas básicas
    total_customers = db.query(CustomerProfile).filter(
        CustomerProfile.shop_id == shop_id
    ).count()
    
    active_customers = db.query(CustomerProfile).filter(
        CustomerProfile.shop_id == shop_id,
        CustomerProfile.last_interaction >= cutoff_date
    ).count()
    
    # Interacciones recientes
    total_interactions = db.query(ChatInteraction).filter(
        ChatInteraction.shop_id == shop_id,
        ChatInteraction.created_at >= cutoff_date
    ).count()
    
    # Clientes con preferencias de equipos
    customers_with_teams = db.query(CustomerProfile).filter(
        CustomerProfile.shop_id == shop_id,
        CustomerProfile.favorite_teams.isnot(None)
    ).count()
    
    # Equipos más populares
    team_preferences = db.query(CustomerProfile.favorite_teams).filter(
        CustomerProfile.shop_id == shop_id,
        CustomerProfile.favorite_teams.isnot(None)
    ).all()
    
    # Procesar equipos más populares
    team_counts = {}
    for prefs in team_preferences:
        if prefs[0]:  # Si hay equipos favoritos
            for team in prefs[0]:
                team_counts[team] = team_counts.get(team, 0) + 1
    
    top_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "total_interactions": total_interactions,
        "customers_with_team_preferences": customers_with_teams,
        "team_preference_rate": customers_with_teams / total_customers if total_customers > 0 else 0,
        "top_teams": top_teams,
        "period_days": days
    }

async def backup_database(backup_path: str = None):
    """
    Crea un backup de la base de datos
    """
    try:
        if DATABASE_URL.startswith("sqlite"):
            import shutil
            from datetime import datetime
            
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{db_path}.backup_{timestamp}"
            
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return {"status": "success", "backup_path": backup_path}
            
        else:
            # Para PostgreSQL, usar pg_dump
            import subprocess
            from datetime import datetime
            
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{timestamp}.sql"
            
            # Extraer info de conexión de DATABASE_URL
            # postgresql://user:password@host:port/database
            import urllib.parse
            parsed = urllib.parse.urlparse(DATABASE_URL)
            
            env = {
                "PGPASSWORD": parsed.password
            }
            
            cmd = [
                "pg_dump",
                "-h", parsed.hostname,
                "-p", str(parsed.port),
                "-U", parsed.username,
                "-d", parsed.path[1:],  # Remove leading /
                "-f", backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backed up to: {backup_path}")
                return {"status": "success", "backup_path": backup_path}
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return {"status": "error", "error": result.stderr}
                
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return {"status": "error", "error": str(e)}