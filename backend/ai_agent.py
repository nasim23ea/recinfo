"""
Agente de IA Principal
Procesa consultas combinando datos de Shopify y deportivos
"""

import openai
from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AIAgent:
    """
    Agente de IA que combina datos de Shopify con información deportiva
    para proporcionar recomendaciones y análisis inteligentes
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI()
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Carga el prompt del sistema que define el comportamiento del agente"""
        return """
        Eres un agente de IA especializado en ecommerce deportivo que integra datos de Shopify 
        con información de equipos universitarios de fútbol americano.
        
        CAPACIDADES:
        - Analizar datos de ventas y correlacionarlos con rendimiento deportivo
        - Recomendar productos basados en equipos favoritos y rendimiento reciente
        - Proporcionar insights de marketing deportivo
        - Asistir en atención al cliente con conocimiento deportivo
        - Predecir tendencias de ventas basadas en calendario deportivo
        
        DATOS DISPONIBLES:
        - Productos, pedidos, clientes e inventario de Shopify
        - Información de 130+ equipos universitarios
        - Resultados históricos de partidos
        - Estadísticas de rendimiento de equipos
        
        INSTRUCCIONES:
        - Siempre combina datos comerciales con insights deportivos
        - Proporciona recomendaciones específicas y accionables
        - Mantén un tono profesional pero entusiasta sobre deportes
        - Cita datos específicos cuando sea posible
        - Sugiere acciones de marketing cuando sea relevante
        """
    
    async def process_message(
        self, 
        message: str,
        shopify_context: Dict[str, Any],
        sports_context: Dict[str, Any],
        customer_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario combinando todos los contextos disponibles
        """
        try:
            # Construir contexto completo
            full_context = self._build_context(
                shopify_context, 
                sports_context, 
                customer_id, 
                additional_context
            )
            
            # Generar respuesta con OpenAI
            response = await self._generate_ai_response(message, full_context)
            
            # Procesar y estructurar la respuesta
            structured_response = await self._structure_response(response, full_context)
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                "text": "Lo siento, ocurrió un error procesando tu consulta. Por favor intenta de nuevo.",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _build_context(
        self,
        shopify_context: Dict[str, Any],
        sports_context: Dict[str, Any],
        customer_id: Optional[str],
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """Construye el contexto completo para el agente"""
        
        context_parts = []
        
        # Contexto de Shopify
        if shopify_context:
            context_parts.append("DATOS DE SHOPIFY:")
            context_parts.append(f"- Tienda: {shopify_context.get('shop_name', 'N/A')}")
            context_parts.append(f"- Total productos: {shopify_context.get('product_count', 0)}")
            context_parts.append(f"- Pedidos recientes: {shopify_context.get('recent_orders', 0)}")
            
            if shopify_context.get('popular_products'):
                context_parts.append("- Productos populares:")
                for product in shopify_context['popular_products'][:3]:
                    context_parts.append(f"  * {product.get('title', 'Sin título')}")
        
        # Contexto deportivo
        if sports_context:
            context_parts.append("\nDATOS DEPORTIVOS:")
            if sports_context.get('relevant_teams'):
                for team in sports_context['relevant_teams']:
                    context_parts.append(f"- {team['name']}: {team.get('record', 'N/A')}")
                    
            if sports_context.get('recent_games'):
                context_parts.append("- Juegos recientes relevantes:")
                for game in sports_context['recent_games'][:3]:
                    context_parts.append(f"  * {game}")
        
        # Contexto del cliente
        if customer_id and additional_context:
            customer_info = additional_context.get('customer_info', {})
            if customer_info:
                context_parts.append(f"\nCLIENTE:")
                context_parts.append(f"- ID: {customer_id}")
                context_parts.append(f"- Compras previas: {customer_info.get('order_count', 0)}")
                if customer_info.get('favorite_teams'):
                    context_parts.append(f"- Equipos favoritos: {', '.join(customer_info['favorite_teams'])}")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, message: str, context: str) -> str:
        """Genera respuesta usando OpenAI"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"CONTEXTO:\n{context}\n\nCONSULTA: {message}"}
        ]
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    async def _structure_response(self, ai_response: str, context: str) -> Dict[str, Any]:
        """Estructura la respuesta del AI en formato útil"""
        
        # Extraer acciones sugeridas
        actions = self._extract_actions(ai_response)
        
        # Extraer recomendaciones de productos
        recommendations = self._extract_recommendations(ai_response)
        
        # Extraer insights deportivos
        sports_insights = self._extract_sports_insights(ai_response)
        
        # Calcular confianza basada en disponibilidad de datos
        confidence = self._calculate_confidence(context, ai_response)
        
        return {
            "text": ai_response,
            "actions": actions,
            "recommendations": recommendations,
            "sports_insights": sports_insights,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_actions(self, response: str) -> List[str]:
        """Extrae acciones sugeridas de la respuesta"""
        actions = []
        
        # Buscar patrones de acciones
        action_patterns = [
            r"deberías?\s+([^.]+)",
            r"te recomiendo\s+([^.]+)",
            r"sugiero\s+([^.]+)",
            r"podrías?\s+([^.]+)"
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            actions.extend(matches)
        
        return actions[:5]  # Máximo 5 acciones
    
    def _extract_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """Extrae recomendaciones de productos de la respuesta"""
        recommendations = []
        
        # Buscar menciones de productos o categorías
        product_patterns = [
            r"camiseta[s]?\s+de\s+([^,.]+)",
            r"productos?\s+de\s+([^,.]+)",
            r"mercancía\s+de\s+([^,.]+)"
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                recommendations.append({
                    "type": "product_category",
                    "value": match.strip(),
                    "confidence": 0.8
                })
        
        return recommendations[:3]  # Máximo 3 recomendaciones
    
    def _extract_sports_insights(self, response: str) -> Dict[str, Any]:
        """Extrae insights deportivos de la respuesta"""
        insights = {}
        
        # Buscar menciones de equipos
        team_mentions = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', response)
        insights["mentioned_teams"] = list(set(team_mentions))[:5]
        
        # Buscar términos relacionados con rendimiento
        performance_terms = ["ganar", "perder", "victoria", "derrota", "temporada", "ranking"]
        mentioned_terms = [term for term in performance_terms if term in response.lower()]
        insights["performance_context"] = mentioned_terms
        
        return insights
    
    def _calculate_confidence(self, context: str, response: str) -> float:
        """Calcula el nivel de confianza de la respuesta"""
        confidence = 0.5  # Base
        
        # Aumentar confianza si hay datos de Shopify
        if "DATOS DE SHOPIFY" in context:
            confidence += 0.2
        
        # Aumentar confianza si hay datos deportivos
        if "DATOS DEPORTIVOS" in context:
            confidence += 0.2
        
        # Aumentar confianza si la respuesta incluye datos específicos
        if re.search(r'\d+', response):  # Contiene números
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def generate_product_recommendations(
        self,
        team_info: Optional[Dict[str, Any]],
        available_products: List[Dict[str, Any]],
        customer_preferences: Optional[List[str]],
        include_recent_performance: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones específicas de productos
        """
        try:
            # Construir prompt para recomendaciones
            prompt = self._build_recommendation_prompt(
                team_info, available_products, customer_preferences, include_recent_performance
            )
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en marketing deportivo y ecommerce."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Procesar recomendaciones
            recommendations_text = response.choices[0].message.content
            recommendations = self._parse_recommendations(recommendations_text, available_products)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return []
    
    def _build_recommendation_prompt(
        self,
        team_info: Optional[Dict[str, Any]],
        available_products: List[Dict[str, Any]],
        customer_preferences: Optional[List[str]],
        include_recent_performance: bool
    ) -> str:
        """Construye prompt para generar recomendaciones"""
        
        prompt_parts = [
            "Genera recomendaciones de productos deportivos basadas en:",
            f"\nPRODUCTOS DISPONIBLES ({len(available_products)} total):"
        ]
        
        # Listar productos disponibles
        for i, product in enumerate(available_products[:10]):  # Máximo 10 para el prompt
            prompt_parts.append(f"{i+1}. {product.get('title', 'Sin título')} - ${product.get('price', 'N/A')}")
        
        # Información del equipo
        if team_info:
            prompt_parts.append(f"\nINFO DEL EQUIPO:")
            prompt_parts.append(f"- Nombre: {team_info.get('name', 'N/A')}")
            prompt_parts.append(f"- Record: {team_info.get('record', 'N/A')}")
            
            if include_recent_performance and team_info.get('recent_games'):
                prompt_parts.append("- Juegos recientes:")
                for game in team_info['recent_games'][:3]:
                    prompt_parts.append(f"  * {game}")
        
        # Preferencias del cliente
        if customer_preferences:
            prompt_parts.append(f"\nPREFERENCIAS DEL CLIENTE:")
            for pref in customer_preferences:
                prompt_parts.append(f"- {pref}")
        
        prompt_parts.append("\nGenera 3-5 recomendaciones con razones específicas.")
        
        return "\n".join(prompt_parts)
    
    def _parse_recommendations(
        self, 
        recommendations_text: str, 
        available_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parsea las recomendaciones del texto de respuesta"""
        
        recommendations = []
        lines = recommendations_text.split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            
            # Buscar números de productos mencionados
            product_nums = re.findall(r'\b(\d+)\b', line)
            for num in product_nums:
                idx = int(num) - 1
                if 0 <= idx < len(available_products):
                    product = available_products[idx]
                    current_rec = {
                        "product_id": product.get('id'),
                        "title": product.get('title'),
                        "price": product.get('price'),
                        "reason": line,
                        "confidence": 0.8
                    }
                    recommendations.append(current_rec)
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    async def analyze_sales_correlation(
        self,
        sales_data: Dict[str, Any],
        team_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analiza correlación entre ventas y rendimiento deportivo
        """
        try:
            # Construir prompt de análisis
            analysis_prompt = f"""
            Analiza la correlación entre ventas y rendimiento deportivo:
            
            DATOS DE VENTAS:
            - Ventas totales: ${sales_data.get('total', 0)}
            - Número de pedidos: {sales_data.get('order_count', 0)}
            - Productos más vendidos: {sales_data.get('top_products', [])}
            
            RENDIMIENTO DEPORTIVO:
            - Equipo: {team_performance.get('team_name', 'N/A')}
            - Record: {team_performance.get('record', 'N/A')}
            - Últimos juegos: {team_performance.get('recent_games', [])}
            
            Proporciona:
            1. Análisis de correlación
            2. Impacto del rendimiento en ventas
            3. Recomendaciones de marketing
            4. Predicciones para próximos juegos
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un analista de datos especializado en marketing deportivo."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Estructurar análisis
            return {
                "correlation_strength": self._extract_correlation_strength(analysis_text),
                "performance_impact": self._extract_performance_impact(analysis_text),
                "recommendations": self._extract_marketing_recommendations(analysis_text),
                "predictions": self._extract_predictions(analysis_text),
                "full_analysis": analysis_text
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de correlación: {e}")
            return {"error": str(e)}
    
    def _extract_correlation_strength(self, text: str) -> str:
        """Extrae la fuerza de correlación del análisis"""
        patterns = ["fuerte", "moderada", "débil", "alta", "baja"]
        for pattern in patterns:
            if pattern in text.lower():
                return pattern
        return "moderada"
    
    def _extract_performance_impact(self, text: str) -> Dict[str, Any]:
        """Extrae el impacto del rendimiento en ventas"""
        impact = {}
        
        # Buscar porcentajes
        percentages = re.findall(r'(\d+)%', text)
        if percentages:
            impact["sales_increase"] = f"{percentages[0]}%"
        
        # Buscar términos de impacto
        if "positivo" in text.lower():
            impact["direction"] = "positive"
        elif "negativo" in text.lower():
            impact["direction"] = "negative"
        else:
            impact["direction"] = "neutral"
        
        return impact
    
    def _extract_marketing_recommendations(self, text: str) -> List[str]:
        """Extrae recomendaciones de marketing del análisis"""
        recommendations = []
        
        # Buscar líneas que empiecen con números o bullets
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                recommendations.append(line)
        
        return recommendations[:5]
    
    def _extract_predictions(self, text: str) -> List[str]:
        """Extrae predicciones del análisis"""
        predictions = []
        
        # Buscar frases con palabras clave de predicción
        prediction_words = ["espera", "predict", "anticipa", "proyecta"]
        sentences = text.split('.')
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in prediction_words):
                predictions.append(sentence.strip())
        
        return predictions[:3]
    
    async def analyze_order_team_preferences(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las preferencias de equipos basadas en un pedido"""
        try:
            # Extraer información de productos del pedido
            products = order_data.get('line_items', [])
            product_titles = [item.get('title', '') for item in products]
            
            # Usar IA para determinar equipos asociados
            analysis_prompt = f"""
            Analiza estos productos para determinar qué equipos deportivos prefiere el cliente:
            
            PRODUCTOS COMPRADOS:
            {chr(10).join(f"- {title}" for title in product_titles)}
            
            Identifica:
            1. Equipos mencionados o asociados
            2. Nivel de lealtad del fan (casual, moderado, fanático)
            3. Categorías de productos preferidas
            4. Sugerencias para futuras compras
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de comportamiento de fans deportivos."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "analysis": analysis,
                "order_total": order_data.get('total_price', 0),
                "product_count": len(products),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando preferencias del pedido: {e}")
            return {"error": str(e)}
    
    async def infer_sports_preferences(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Infiere preferencias deportivas de un nuevo cliente"""
        try:
            # Analizar información disponible del cliente
            location = customer_data.get('default_address', {})
            name = customer_data.get('first_name', '') + ' ' + customer_data.get('last_name', '')
            
            inference_prompt = f"""
            Basándote en la información limitada de este nuevo cliente, 
            sugiere posibles preferencias deportivas:
            
            INFORMACIÓN DEL CLIENTE:
            - Nombre: {name.strip()}
            - Ciudad: {location.get('city', 'N/A')}
            - Estado/Provincia: {location.get('province', 'N/A')}
            - País: {location.get('country', 'N/A')}
            
            Sugiere:
            1. Equipos locales probables
            2. Categorías de productos que podrían interesar
            3. Estrategias de marketing personalizadas
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un especialista en marketing deportivo personalizado."},
                    {"role": "user", "content": inference_prompt}
                ],
                temperature=0.5
            )
            
            return {
                "inferred_preferences": response.choices[0].message.content,
                "customer_id": customer_data.get('id'),
                "location": location,
                "confidence": 0.6  # Baja confianza por datos limitados
            }
            
        except Exception as e:
            logger.error(f"Error infiriendo preferencias: {e}")
            return {"error": str(e)}