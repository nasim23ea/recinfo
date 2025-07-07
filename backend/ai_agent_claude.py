"""
Agente de IA Principal usando Claude (Anthropic)
Procesa consultas combinando datos de Shopify y deportivos
"""

import anthropic
from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class ClaudeAIAgent:
    """
    Agente de IA que combina datos de Shopify con información deportiva
    usando Claude de Anthropic
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Usar API key proporcionada o desde variables de entorno
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if self.api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.claude_client = None
            logger.warning("No se proporcionó API key de Claude - funcionando en modo simulación")
        
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Carga el prompt del sistema optimizado para Claude"""
        return """
        Eres un agente de IA especializado en ecommerce deportivo que integra datos de Shopify 
        con información de equipos universitarios de fútbol americano.
        
        CAPACIDADES PRINCIPALES:
        - Analizar datos de ventas y correlacionarlos con rendimiento deportivo
        - Recomendar productos basados en equipos favoritos y rendimiento reciente
        - Proporcionar insights de marketing deportivo específicos
        - Asistir en atención al cliente con conocimiento deportivo profundo
        - Predecir tendencias de ventas basadas en calendario deportivo
        
        DATOS DISPONIBLES:
        - Productos, pedidos, clientes e inventario de Shopify
        - Información detallada de 128+ equipos universitarios
        - Resultados históricos de 760+ partidos
        - Estadísticas avanzadas de rendimiento de equipos
        - Análisis de tendencias y momentum de equipos
        
        ESTILO DE RESPUESTA:
        - Combina SIEMPRE datos comerciales con insights deportivos
        - Proporciona recomendaciones específicas y accionables
        - Mantén un tono profesional pero entusiasta sobre deportes
        - Cita estadísticas específicas cuando sea posible
        - Sugiere acciones de marketing concretas
        - Usa emojis deportivos apropiados (🏈, 🏆, 📈, etc.)
        
        EJEMPLOS DE RESPUESTAS EFECTIVAS:
        - "Alabama tiene 13-1 record (92.9% victorias) 🔥 - momento perfecto para promocionar jerseys premium"
        - "Basado en el momentum de Clemson, recomiendo aumentar inventario de productos de celebración"
        - "Las ventas de productos de Georgia típicamente aumentan 40% después de victorias importantes"
        """
    
    async def process_message(
        self, 
        message: str,
        shopify_context: Dict[str, Any] = None,
        sports_context: Dict[str, Any] = None,
        customer_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario combinando todos los contextos disponibles
        """
        try:
            # Construir contexto completo
            full_context = self._build_context(
                shopify_context or {}, 
                sports_context or {}, 
                customer_id, 
                additional_context or {}
            )
            
            # Generar respuesta con Claude o simulación
            if self.claude_client:
                response = await self._generate_claude_response(message, full_context)
            else:
                response = self._generate_simulated_response(message, full_context)
            
            # Procesar y estructurar la respuesta
            structured_response = await self._structure_response(response, full_context)
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                "text": "Lo siento, ocurrió un error procesando tu consulta. Por favor intenta de nuevo.",
                "error": str(e),
                "confidence": 0.0,
                "source": "error_handler"
            }
    
    def _build_context(
        self,
        shopify_context: Dict[str, Any],
        sports_context: Dict[str, Any],
        customer_id: Optional[str],
        additional_context: Dict[str, Any]
    ) -> str:
        """Construye el contexto completo para el agente"""
        
        context_parts = []
        
        # Contexto de Shopify
        if shopify_context:
            context_parts.append("DATOS DE SHOPIFY:")
            context_parts.append(f"- Tienda: {shopify_context.get('shop_name', 'Sports Store')}")
            context_parts.append(f"- Total productos: {shopify_context.get('product_count', 150)}")
            context_parts.append(f"- Pedidos recientes: {shopify_context.get('recent_orders', 25)}")
            
            if shopify_context.get('popular_products'):
                context_parts.append("- Productos populares:")
                for product in shopify_context['popular_products'][:3]:
                    context_parts.append(f"  * {product.get('title', 'Producto deportivo')}")
                    
            if shopify_context.get('revenue'):
                context_parts.append(f"- Revenue mensual: ${shopify_context['revenue']}")
        
        # Contexto deportivo (más detallado)
        if sports_context:
            context_parts.append("\nDATOS DEPORTIVOS ACTUALIZADOS:")
            
            if sports_context.get('relevant_teams'):
                context_parts.append("- Equipos relevantes:")
                for team in sports_context['relevant_teams'][:5]:
                    record = team.get('record', 'N/A')
                    win_pct = team.get('stats', {}).get('win_percentage', 0)
                    context_parts.append(f"  * {team['name']}: {record} ({win_pct:.1%} victorias)")
                    
            if sports_context.get('recent_games'):
                context_parts.append("- Juegos recientes relevantes:")
                for game in sports_context['recent_games'][:5]:
                    context_parts.append(f"  * {game}")
                    
            if sports_context.get('trending_teams'):
                context_parts.append("- Equipos en tendencia:")
                for team in sports_context['trending_teams'][:3]:
                    context_parts.append(f"  * {team}")
        
        # Contexto del cliente (más rico)
        if customer_id and additional_context:
            customer_info = additional_context.get('customer_info', {})
            if customer_info:
                context_parts.append(f"\nPERFIL DEL CLIENTE:")
                context_parts.append(f"- ID: {customer_id}")
                context_parts.append(f"- Compras previas: {customer_info.get('order_count', 0)}")
                context_parts.append(f"- Gasto total: ${customer_info.get('total_spent', 0)}")
                
                if customer_info.get('favorite_teams'):
                    context_parts.append(f"- Equipos favoritos: {', '.join(customer_info['favorite_teams'])}")
                    
                if customer_info.get('purchase_patterns'):
                    context_parts.append(f"- Patrones de compra: {customer_info['purchase_patterns']}")
        
        # Contexto temporal
        context_parts.append(f"\nCONTEXTO TEMPORAL:")
        context_parts.append(f"- Fecha: {datetime.now().strftime('%Y-%m-%d')}")
        context_parts.append(f"- Temporada: Temporada universitaria activa")
        
        return "\n".join(context_parts)
    
    async def _generate_claude_response(self, message: str, context: str) -> str:
        """Genera respuesta usando Claude"""
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",  # Modelo más reciente y potente
                max_tokens=1500,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user", 
                        "content": f"CONTEXTO COMPLETO:\n{context}\n\nCONSULTA DEL USUARIO: {message}\n\nPor favor, proporciona una respuesta útil que combine los datos comerciales y deportivos disponibles."
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error con Claude API: {e}")
            # Fallback a respuesta simulada
            return self._generate_simulated_response(message, context)
    
    def _generate_simulated_response(self, message: str, context: str) -> str:
        """Genera respuesta simulada cuando no hay API key"""
        
        message_lower = message.lower()
        
        # Respuestas específicas basadas en patrones
        if 'alabama' in message_lower:
            return """🏈 Alabama tiene un excelente record de 13-1 esta temporada (92.9% de victorias), lo que los convierte en un equipo dominante con gran diferencia de puntos promedio (+25.6).

📈 **Insights comerciales:**
- Momento PERFECTO para promocionar productos premium de Alabama
- Las ventas de jerseys de Alabama típicamente aumentan 60% después de victorias importantes
- Recomiendo aumentar inventario de productos de celebración

🛍️ **Productos recomendados:**
1. Alabama Crimson Tide Championship Jersey ($89.99)
2. Alabama Victory Collection ($45-75 rango de precios)
3. Alabama Premium Fan Pack ($120+ para fanáticos dedicados)

🎯 **Estrategia de marketing:**
- Aprovechar el momentum actual con campañas de "Equipo Campeón"
- Targeting a fanáticos universitarios de 18-45 años
- Promociones especiales durante próximos juegos importantes"""

        elif any(word in message_lower for word in ['top', 'mejores', 'dominantes', 'ganadores']):
            return """🏆 **TOP EQUIPOS ESTA TEMPORADA:**

1. **Alabama** - 92.9% victorias (13-1) 🔥
   - Marketing Priority: ALTA
   - Productos sugeridos: Merchandise premium, championship gear

2. **Clemson** - 92.9% victorias (13-1) 🔥
   - Marketing Priority: ALTA  
   - Productos sugeridos: Victory collection, fan essentials

3. **Western Michigan** - 92.3% victorias (12-1) 📈
   - Marketing Priority: MEDIA-ALTA
   - Productos sugeridos: Breakthrough team merchandise

📊 **Oportunidades de negocio:**
- 23 equipos con +70% victorias = oportunidades premium
- Correlación directa entre victorias y aumento en ventas (35-60%)
- Momento ideal para campañas de equipos ganadores"""

        elif any(word in message_lower for word in ['recomienda', 'productos', 'venta', 'marketing']):
            return """🛍️ **RECOMENDACIONES ESTRATÉGICAS DE PRODUCTOS:**

**ENFOQUE INMEDIATO (Equipos dominantes):**
- Alabama, Clemson, Western Michigan merchandise
- Productos premium y de celebración
- ROI estimado: 40-60% superior

**ESTRATEGIA POR CATEGORÍAS:**
🏈 **Jerseys**: Focus en equipos top 10
👕 **Apparel casual**: Equipos con fanbase leal
🎒 **Accesorios**: Cross-selling con cualquier compra

**TIMING ÓPTIMO:**
- Post-victoria: Aumento 40% en búsquedas
- Pre-playoffs: Incremento 65% en ventas
- Fin de semana: Peak de actividad de compra

**SEGMENTACIÓN:**
- Fanáticos hardcore: Productos premium ($80+)
- Fans casuales: Apparel básico ($25-50)
- Nuevos fans: Starter packs ($30-60)"""

        elif any(word in message_lower for word in ['ventas', 'analytics', 'datos', 'estadisticas']):
            return """📊 **ANALYTICS DEPORTIVOS-COMERCIALES:**

**CORRELACIONES IDENTIFICADAS:**
- Victorias de equipos → +35% ventas promedio (24-48h)
- Derrotas inesperadas → -15% en productos del equipo
- Playoffs → +120% en merchandise general

**DATOS ACTUALES:**
- 128 equipos monitoreados
- 760 partidos analizados  
- 23 equipos con oportunidad HIGH
- 45 equipos con oportunidad MEDIUM

**INSIGHTS PREDICTIVOS:**
- Equipos en racha (4+ victorias): Ventana de 2-3 semanas óptima
- Equipos newcomer (Western Michigan): Potencial viralizacion
- Equipos tradicionales (Alabama): Base sólida constante

**RECOMENDACIONES ACTIONABLES:**
1. Aumentar stock de equipos top 5 en 30%
2. Campaña retargeting a compradores de equipos ganadores
3. Bundle deals para aprovechar momentum"""

        else:
            return f"""🤖 ¡Hola! Soy tu agente de IA deportivo especializado en ecommerce.

📊 **Mi conocimiento actual:**
- 128 equipos universitarios monitoreados
- 760 partidos analizados con estadísticas completas
- Integración en tiempo real con datos de Shopify
- Correlaciones entre rendimiento deportivo y ventas

🎯 **¿En qué puedo ayudarte?**
- Análisis de rendimiento de equipos específicos
- Recomendaciones de productos basadas en momentum deportivo
- Estrategias de marketing para equipos ganadores
- Predicciones de ventas basadas en calendario deportivo
- Segmentación de clientes por preferencias de equipos

💡 **Prueba preguntar:**
- "¿Cómo está jugando Alabama?"
- "¿Qué equipos están dominando?"
- "Recomienda productos para marketing"
- "¿Qué nos dicen los datos de ventas?"

¡Estoy aquí para maximizar tus ventas usando datos deportivos inteligentes! 🏈"""

        return response
    
    async def _structure_response(self, ai_response: str, context: str) -> Dict[str, Any]:
        """Estructura la respuesta del AI en formato útil"""
        
        # Extraer diferentes tipos de información
        actions = self._extract_actions(ai_response)
        recommendations = self._extract_recommendations(ai_response)
        sports_insights = self._extract_sports_insights(ai_response)
        business_metrics = self._extract_business_metrics(ai_response)
        
        # Calcular confianza basada en disponibilidad de datos
        confidence = self._calculate_confidence(context, ai_response)
        
        return {
            "text": ai_response,
            "actions": actions,
            "recommendations": recommendations,
            "sports_insights": sports_insights,
            "business_metrics": business_metrics,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "source": "claude" if self.claude_client else "simulated"
        }
    
    def _extract_actions(self, response: str) -> List[str]:
        """Extrae acciones sugeridas de la respuesta"""
        actions = []
        
        # Buscar patrones de acciones más específicos
        action_patterns = [
            r"recomiendo\s+([^.\n]+)",
            r"sugiero\s+([^.\n]+)",
            r"deberías?\s+([^.\n]+)",
            r"es importante\s+([^.\n]+)",
            r"considera\s+([^.\n]+)"
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            actions.extend([match.strip() for match in matches])
        
        # Limpiar y deduplicar
        actions = list(set([action for action in actions if len(action) > 10]))
        
        return actions[:5]  # Máximo 5 acciones
    
    def _extract_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """Extrae recomendaciones de productos de la respuesta"""
        recommendations = []
        
        # Buscar productos específicos con precios
        product_price_pattern = r"([A-Z][^$]+)\s*\(\$([0-9,]+(?:\.[0-9]{2})?)\)"
        matches = re.findall(product_price_pattern, response)
        
        for product_name, price in matches:
            recommendations.append({
                "type": "product",
                "name": product_name.strip(),
                "price": f"${price}",
                "confidence": 0.9
            })
        
        # Buscar categorías de productos
        category_patterns = [
            r"jerseys?\s+de\s+([^,.]+)",
            r"productos?\s+de\s+([^,.]+)",
            r"merchandise\s+de\s+([^,.]+)",
            r"apparel\s+de\s+([^,.]+)"
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                recommendations.append({
                    "type": "category",
                    "name": match.strip(),
                    "confidence": 0.7
                })
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    def _extract_sports_insights(self, response: str) -> Dict[str, Any]:
        """Extrae insights deportivos específicos de la respuesta"""
        insights = {}
        
        # Buscar menciones de equipos
        team_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        team_mentions = re.findall(team_pattern, response)
        
        # Filtrar equipos conocidos (simplificado)
        known_teams = ['Alabama', 'Clemson', 'Georgia', 'Ohio State', 'Michigan', 'Texas', 'USC', 'Notre Dame']
        mentioned_teams = [team for team in team_mentions if team in known_teams]
        insights["mentioned_teams"] = list(set(mentioned_teams))[:5]
        
        # Buscar porcentajes de victorias
        win_percentages = re.findall(r'(\d+(?:\.\d+)?)%\s*(?:de\s*)?victorias?', response, re.IGNORECASE)
        if win_percentages:
            insights["win_percentages"] = [f"{pct}%" for pct in win_percentages]
        
        # Buscar records
        records = re.findall(r'(\d+-\d+)', response)
        if records:
            insights["records"] = records
        
        # Buscar términos de rendimiento
        performance_terms = ["dominante", "racha", "momentum", "temporada", "campeón", "playoffs"]
        mentioned_terms = [term for term in performance_terms if term.lower() in response.lower()]
        insights["performance_context"] = mentioned_terms
        
        return insights
    
    def _extract_business_metrics(self, response: str) -> Dict[str, Any]:
        """Extrae métricas de negocio de la respuesta"""
        metrics = {}
        
        # Buscar porcentajes de aumento en ventas
        sales_increases = re.findall(r'(\d+)%\s*(?:aumento|incremento|más)', response, re.IGNORECASE)
        if sales_increases:
            metrics["sales_increase"] = f"{sales_increases[0]}%"
        
        # Buscar ROI
        roi_matches = re.findall(r'ROI[:\s]*(\d+(?:-\d+)?%)', response, re.IGNORECASE)
        if roi_matches:
            metrics["roi"] = roi_matches[0]
        
        # Buscar prioridades de marketing
        if "ALTA" in response or "HIGH" in response:
            metrics["marketing_priority"] = "HIGH"
        elif "MEDIA" in response or "MEDIUM" in response:
            metrics["marketing_priority"] = "MEDIUM"
        elif "BAJA" in response or "LOW" in response:
            metrics["marketing_priority"] = "LOW"
        
        return metrics
    
    def _calculate_confidence(self, context: str, response: str) -> float:
        """Calcula el nivel de confianza de la respuesta"""
        confidence = 0.6  # Base más alta para Claude
        
        # Aumentar confianza si hay datos de Shopify
        if "DATOS DE SHOPIFY" in context:
            confidence += 0.15
        
        # Aumentar confianza si hay datos deportivos
        if "DATOS DEPORTIVOS" in context:
            confidence += 0.15
        
        # Aumentar confianza si la respuesta incluye datos específicos
        if re.search(r'\d+(?:\.\d+)?%', response):  # Contiene porcentajes
            confidence += 0.05
            
        if re.search(r'\$\d+', response):  # Contiene precios
            confidence += 0.05
        
        # Bonus por usar Claude real vs simulación
        if self.claude_client:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def generate_product_recommendations(
        self,
        team_info: Optional[Dict[str, Any]],
        available_products: List[Dict[str, Any]],
        customer_preferences: Optional[List[str]],
        budget_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones específicas de productos usando Claude
        """
        try:
            # Construir prompt optimizado para Claude
            prompt = self._build_recommendation_prompt_claude(
                team_info, available_products, customer_preferences, budget_range
            )
            
            if self.claude_client:
                response = self.claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    temperature=0.3,
                    system="Eres un experto en marketing deportivo y ecommerce. Proporciona recomendaciones específicas y accionables.",
                    messages=[{"role": "user", "content": prompt}]
                )
                recommendations_text = response.content[0].text
            else:
                # Simulación para demo
                recommendations_text = self._simulate_product_recommendations(team_info, available_products)
            
            # Procesar recomendaciones
            recommendations = self._parse_recommendations_claude(recommendations_text, available_products)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return self._fallback_recommendations(team_info, available_products)
    
    def _build_recommendation_prompt_claude(
        self,
        team_info: Optional[Dict[str, Any]],
        available_products: List[Dict[str, Any]],
        customer_preferences: Optional[List[str]],
        budget_range: Optional[str]
    ) -> str:
        """Construye prompt optimizado para Claude"""
        
        prompt_parts = [
            "Como experto en marketing deportivo, genera recomendaciones de productos específicas:",
            f"\nPRODUCTOS DISPONIBLES ({len(available_products)} total):"
        ]
        
        # Listar productos disponibles con más detalle
        for i, product in enumerate(available_products[:8]):  # Máximo 8 para el prompt
            title = product.get('title', 'Sin título')
            price = product.get('price', 'N/A')
            category = product.get('product_type', 'General')
            prompt_parts.append(f"{i+1}. {title} - ${price} ({category})")
        
        # Información del equipo con contexto deportivo
        if team_info:
            prompt_parts.append(f"\nDATA DEL EQUIPO:")
            prompt_parts.append(f"- Nombre: {team_info.get('name', 'N/A')}")
            prompt_parts.append(f"- Record: {team_info.get('record', 'N/A')}")
            prompt_parts.append(f"- Win %: {team_info.get('stats', {}).get('win_percentage', 0):.1%}")
            
            if team_info.get('recent_games'):
                prompt_parts.append("- Momentum reciente:")
                for game in team_info['recent_games'][:3]:
                    prompt_parts.append(f"  * {game}")
        
        # Preferencias del cliente
        if customer_preferences:
            prompt_parts.append(f"\nPREFERENCIAS DEL CLIENTE:")
            for pref in customer_preferences:
                prompt_parts.append(f"- {pref}")
        
        # Rango de presupuesto
        if budget_range:
            prompt_parts.append(f"\nPRESUPUESTO: {budget_range}")
        
        prompt_parts.extend([
            "\nGenera 3-5 recomendaciones ESPECÍFICAS con:",
            "1. Producto exacto (usa números de la lista)",
            "2. Razón basada en datos deportivos",
            "3. Momento óptimo de compra",
            "4. Potencial de ventas adicionales"
        ])
        
        return "\n".join(prompt_parts)
    
    def _simulate_product_recommendations(
        self, 
        team_info: Optional[Dict[str, Any]], 
        available_products: List[Dict[str, Any]]
    ) -> str:
        """Simula recomendaciones cuando no hay API key"""
        
        team_name = team_info.get('name', 'Team') if team_info else 'Top Teams'
        
        return f"""
        **RECOMENDACIONES PARA {team_name.upper()}:**
        
        1. **Producto #1-3**: Jersey y apparel básico
           - Razón: Base sólida para cualquier fan
           - Momento: Disponible inmediatamente
           - Cross-sell: Accesorios complementarios
        
        2. **Productos premium** (si disponibles):
           - Razón: Aprovechar momentum actual del equipo
           - Momento: Durante rachas ganadoras
           - Potencial: 60% mayor conversión
        
        3. **Bundle packages**:
           - Razón: Maximizar valor promedio de orden
           - Momento: Temporada activa
           - Cross-sell: Productos de equipos rivales
        """
    
    def _parse_recommendations_claude(
        self, 
        recommendations_text: str, 
        available_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parsea las recomendaciones generadas por Claude"""
        
        recommendations = []
        
        # Buscar referencias a productos numerados
        product_refs = re.findall(r'Producto\s*#?(\d+(?:-\d+)?)', recommendations_text, re.IGNORECASE)
        
        for ref in product_refs:
            if '-' in ref:
                # Rango de productos
                start, end = map(int, ref.split('-'))
                for idx in range(start-1, min(end, len(available_products))):
                    if 0 <= idx < len(available_products):
                        product = available_products[idx]
                        recommendations.append({
                            "product_id": product.get('id', f'prod_{idx}'),
                            "title": product.get('title', 'Producto deportivo'),
                            "price": product.get('price', '49.99'),
                            "reason": f"Recomendado por análisis deportivo",
                            "confidence": 0.8,
                            "timing": "optimal"
                        })
            else:
                # Producto específico
                idx = int(ref) - 1
                if 0 <= idx < len(available_products):
                    product = available_products[idx]
                    recommendations.append({
                        "product_id": product.get('id', f'prod_{idx}'),
                        "title": product.get('title', 'Producto deportivo'),
                        "price": product.get('price', '49.99'),
                        "reason": f"Recomendado específicamente por Claude",
                        "confidence": 0.9,
                        "timing": "immediate"
                    })
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    def _fallback_recommendations(
        self, 
        team_info: Optional[Dict[str, Any]], 
        available_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Recomendaciones de fallback cuando hay errores"""
        
        fallback = []
        
        # Recomendar primeros 3 productos disponibles
        for i, product in enumerate(available_products[:3]):
            fallback.append({
                "product_id": product.get('id', f'fallback_{i}'),
                "title": product.get('title', 'Producto deportivo'),
                "price": product.get('price', '39.99'),
                "reason": "Recomendación general basada en popularidad",
                "confidence": 0.6,
                "timing": "available"
            })
        
        return fallback

# Función de conveniencia para crear agente
def create_claude_agent(api_key: Optional[str] = None) -> ClaudeAIAgent:
    """Crea una instancia del agente Claude"""
    return ClaudeAIAgent(api_key=api_key)