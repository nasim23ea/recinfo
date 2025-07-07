"""
Cliente de Shopify API
Maneja todas las interacciones con las tiendas de Shopify
"""

import shopify
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import os
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ShopifyClient:
    """
    Cliente para interactuar con la API de Shopify
    Maneja autenticación, webhooks y operaciones CRUD
    """
    
    def __init__(self):
        self.api_key = os.getenv('SHOPIFY_API_KEY')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET')
        self.webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET')
        self.api_version = "2024-01"
        
        # Cache para sesiones de tiendas
        self.shop_sessions = {}
    
    async def get_shop_context(self, shop_domain: str) -> Dict[str, Any]:
        """
        Obtiene contexto completo de una tienda para el agente de IA
        """
        try:
            # Configurar sesión de Shopify
            await self._setup_shop_session(shop_domain)
            
            # Obtener información general de la tienda
            shop_info = await self._get_shop_info()
            
            # Obtener productos populares
            popular_products = await self._get_popular_products(limit=10)
            
            # Obtener pedidos recientes
            recent_orders = await self._get_recent_orders(days=30)
            
            # Obtener estadísticas de inventario
            inventory_stats = await self._get_inventory_stats()
            
            return {
                "shop_name": shop_info.get("name"),
                "shop_domain": shop_domain,
                "product_count": shop_info.get("product_count", 0),
                "order_count": len(recent_orders),
                "popular_products": popular_products,
                "recent_orders": len(recent_orders),
                "inventory_stats": inventory_stats,
                "currency": shop_info.get("currency", "USD"),
                "timezone": shop_info.get("timezone"),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto de tienda {shop_domain}: {e}")
            return {"error": str(e)}
    
    async def _setup_shop_session(self, shop_domain: str):
        """Configura la sesión de Shopify para una tienda específica"""
        if shop_domain not in self.shop_sessions:
            # En producción, obtener token de acceso de base de datos
            access_token = os.getenv(f'SHOPIFY_TOKEN_{shop_domain.replace(".", "_").upper()}')
            
            if not access_token:
                raise ValueError(f"No se encontró token de acceso para {shop_domain}")
            
            shopify.ShopifyResource.set_site(f"https://{access_token}@{shop_domain}/admin/api/{self.api_version}")
            self.shop_sessions[shop_domain] = {
                "token": access_token,
                "setup_time": datetime.now()
            }
    
    async def _get_shop_info(self) -> Dict[str, Any]:
        """Obtiene información básica de la tienda"""
        try:
            shop = shopify.Shop.current()
            return {
                "name": shop.name,
                "domain": shop.domain,
                "currency": shop.currency,
                "timezone": shop.timezone,
                "product_count": shop.products_count if hasattr(shop, 'products_count') else 0,
                "customer_count": shop.customer_count if hasattr(shop, 'customer_count') else 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de tienda: {e}")
            return {}
    
    async def _get_popular_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene productos más populares basados en ventas"""
        try:
            # Obtener productos con mejor rendimiento
            products = shopify.Product.find(limit=limit, published_status='published')
            
            product_list = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "title": product.title,
                    "handle": product.handle,
                    "product_type": product.product_type,
                    "vendor": product.vendor,
                    "created_at": str(product.created_at),
                    "updated_at": str(product.updated_at),
                    "tags": product.tags.split(',') if product.tags else [],
                    "images": [img.src for img in product.images] if hasattr(product, 'images') else [],
                    "variants": []
                }
                
                # Agregar variantes
                if hasattr(product, 'variants'):
                    for variant in product.variants:
                        variant_data = {
                            "id": variant.id,
                            "title": variant.title,
                            "price": str(variant.price),
                            "inventory_quantity": variant.inventory_quantity,
                            "sku": variant.sku
                        }
                        product_data["variants"].append(variant_data)
                
                product_list.append(product_data)
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error obteniendo productos populares: {e}")
            return []
    
    async def _get_recent_orders(self, days: int = 30) -> List[Dict[str, Any]]:
        """Obtiene pedidos recientes"""
        try:
            # Calcular fecha límite
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            orders = shopify.Order.find(
                status='any',
                created_at_min=since_date,
                limit=250
            )
            
            order_list = []
            for order in orders:
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_price": str(order.total_price),
                    "subtotal_price": str(order.subtotal_price),
                    "currency": order.currency,
                    "created_at": str(order.created_at),
                    "financial_status": order.financial_status,
                    "fulfillment_status": order.fulfillment_status,
                    "customer_id": order.customer.id if order.customer else None,
                    "line_items_count": len(order.line_items) if order.line_items else 0,
                    "line_items": []
                }
                
                # Agregar artículos del pedido
                if hasattr(order, 'line_items'):
                    for item in order.line_items:
                        item_data = {
                            "product_id": item.product_id,
                            "variant_id": item.variant_id,
                            "title": item.title,
                            "quantity": item.quantity,
                            "price": str(item.price)
                        }
                        order_data["line_items"].append(item_data)
                
                order_list.append(order_data)
            
            return order_list
            
        except Exception as e:
            logger.error(f"Error obteniendo pedidos recientes: {e}")
            return []
    
    async def _get_inventory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de inventario"""
        try:
            # Obtener todos los productos para estadísticas
            products = shopify.Product.find(limit=250)
            
            total_products = len(products)
            low_stock_items = 0
            out_of_stock_items = 0
            total_inventory = 0
            
            for product in products:
                if hasattr(product, 'variants'):
                    for variant in product.variants:
                        quantity = variant.inventory_quantity or 0
                        total_inventory += quantity
                        
                        if quantity == 0:
                            out_of_stock_items += 1
                        elif quantity < 10:  # Definir stock bajo como < 10
                            low_stock_items += 1
            
            return {
                "total_products": total_products,
                "total_inventory": total_inventory,
                "low_stock_items": low_stock_items,
                "out_of_stock_items": out_of_stock_items,
                "average_stock_per_product": total_inventory / total_products if total_products > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de inventario: {e}")
            return {}
    
    async def get_products_by_criteria(
        self,
        team_name: Optional[str] = None,
        budget_range: Optional[tuple] = None,
        product_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Busca productos basados en criterios específicos
        """
        try:
            # Construir parámetros de búsqueda
            search_params = {"limit": limit, "published_status": "published"}
            
            # Filtrar por tipo de producto
            if product_type:
                search_params["product_type"] = product_type
            
            # Buscar productos
            products = shopify.Product.find(**search_params)
            
            filtered_products = []
            for product in products:
                # Filtrar por nombre de equipo en título o tags
                if team_name:
                    team_mentioned = (
                        team_name.lower() in product.title.lower() or
                        team_name.lower() in (product.tags or "").lower()
                    )
                    if not team_mentioned:
                        continue
                
                # Obtener precio mínimo del producto
                min_price = float('inf')
                if hasattr(product, 'variants') and product.variants:
                    for variant in product.variants:
                        price = float(variant.price)
                        min_price = min(min_price, price)
                
                # Filtrar por rango de presupuesto
                if budget_range and min_price != float('inf'):
                    min_budget, max_budget = budget_range
                    if not (min_budget <= min_price <= max_budget):
                        continue
                
                # Agregar producto a resultados
                product_data = {
                    "id": product.id,
                    "title": product.title,
                    "handle": product.handle,
                    "product_type": product.product_type,
                    "vendor": product.vendor,
                    "tags": product.tags.split(',') if product.tags else [],
                    "min_price": min_price if min_price != float('inf') else 0,
                    "images": [img.src for img in product.images] if hasattr(product, 'images') else [],
                    "created_at": str(product.created_at)
                }
                
                filtered_products.append(product_data)
            
            return filtered_products
            
        except Exception as e:
            logger.error(f"Error buscando productos por criterios: {e}")
            return []
    
    async def get_sales_data(
        self,
        team_filter: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Obtiene datos de ventas, opcionalmente filtrados por equipo
        """
        try:
            # Obtener pedidos recientes
            orders = await self._get_recent_orders(days)
            
            total_sales = 0
            order_count = 0
            product_sales = {}
            team_related_sales = 0
            
            for order in orders:
                order_total = float(order.get("total_price", 0))
                total_sales += order_total
                order_count += 1
                
                # Analizar artículos del pedido
                is_team_related = False
                for item in order.get("line_items", []):
                    product_title = item.get("title", "").lower()
                    
                    # Contar ventas por producto
                    if product_title not in product_sales:
                        product_sales[product_title] = {
                            "quantity": 0,
                            "revenue": 0
                        }
                    
                    product_sales[product_title]["quantity"] += item.get("quantity", 0)
                    product_sales[product_title]["revenue"] += float(item.get("price", 0)) * item.get("quantity", 0)
                    
                    # Verificar si está relacionado con el equipo
                    if team_filter and team_filter.lower() in product_title:
                        is_team_related = True
                
                if is_team_related:
                    team_related_sales += order_total
            
            # Obtener productos más vendidos
            top_products = sorted(
                product_sales.items(),
                key=lambda x: x[1]["revenue"],
                reverse=True
            )[:10]
            
            return {
                "total": total_sales,
                "order_count": order_count,
                "average_order_value": total_sales / order_count if order_count > 0 else 0,
                "team_related_sales": team_related_sales,
                "team_percentage": (team_related_sales / total_sales * 100) if total_sales > 0 else 0,
                "top_products": [
                    {
                        "title": product,
                        "quantity_sold": data["quantity"],
                        "revenue": data["revenue"]
                    }
                    for product, data in top_products
                ],
                "period_days": days,
                "currency": "USD"  # Obtener de configuración de tienda
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de ventas: {e}")
            return {"error": str(e)}
    
    async def get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """Obtiene información detallada de un cliente"""
        try:
            customer = shopify.Customer.find(customer_id)
            
            if not customer:
                return {"error": "Cliente no encontrado"}
            
            # Obtener pedidos del cliente
            customer_orders = shopify.Order.find(customer_id=customer_id, limit=50)
            
            # Analizar preferencias de equipos basadas en compras
            team_preferences = {}
            total_spent = 0
            
            for order in customer_orders:
                total_spent += float(order.total_price)
                
                for item in order.line_items:
                    title = item.title.lower()
                    # Lógica simple para detectar nombres de equipos
                    # En producción, usar lógica más sofisticada
                    for team in ["alabama", "georgia", "florida", "auburn", "lsu"]:
                        if team in title:
                            if team not in team_preferences:
                                team_preferences[team] = 0
                            team_preferences[team] += item.quantity
            
            return {
                "id": customer.id,
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "created_at": str(customer.created_at),
                "updated_at": str(customer.updated_at),
                "orders_count": customer.orders_count,
                "total_spent": str(customer.total_spent),
                "verified_email": customer.verified_email,
                "addresses": [
                    {
                        "address1": addr.address1,
                        "city": addr.city,
                        "province": addr.province,
                        "country": addr.country,
                        "zip": addr.zip
                    }
                    for addr in customer.addresses
                ] if hasattr(customer, 'addresses') else [],
                "team_preferences": team_preferences,
                "favorite_teams": list(team_preferences.keys())[:3]  # Top 3 equipos
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información del cliente {customer_id}: {e}")
            return {"error": str(e)}
    
    def verify_webhook(self, data: bytes, signature: str) -> bool:
        """
        Verifica la autenticidad de un webhook de Shopify
        """
        try:
            encoded_secret = self.webhook_secret.encode('utf-8')
            digest = hmac.new(encoded_secret, data, digestmod=hashlib.sha256)
            computed_signature = base64.b64encode(digest.digest()).decode()
            
            return hmac.compare_digest(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verificando webhook: {e}")
            return False
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo producto en Shopify"""
        try:
            product = shopify.Product()
            
            # Configurar atributos del producto
            product.title = product_data.get('title')
            product.body_html = product_data.get('description', '')
            product.vendor = product_data.get('vendor', '')
            product.product_type = product_data.get('product_type', '')
            product.tags = ','.join(product_data.get('tags', []))
            
            # Configurar variantes
            if product_data.get('variants'):
                product.variants = []
                for variant_data in product_data['variants']:
                    variant = shopify.Variant()
                    variant.title = variant_data.get('title', 'Default')
                    variant.price = variant_data.get('price', '0.00')
                    variant.inventory_quantity = variant_data.get('quantity', 0)
                    variant.sku = variant_data.get('sku', '')
                    product.variants.append(variant)
            
            # Guardar producto
            if product.save():
                return {
                    "success": True,
                    "product_id": product.id,
                    "handle": product.handle
                }
            else:
                return {
                    "success": False,
                    "errors": product.errors.full_messages()
                }
                
        except Exception as e:
            logger.error(f"Error creando producto: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_inventory(self, variant_id: str, quantity: int) -> Dict[str, Any]:
        """Actualiza la cantidad de inventario de una variante"""
        try:
            variant = shopify.Variant.find(variant_id)
            variant.inventory_quantity = quantity
            
            if variant.save():
                return {
                    "success": True,
                    "variant_id": variant_id,
                    "new_quantity": quantity
                }
            else:
                return {
                    "success": False,
                    "errors": variant.errors.full_messages()
                }
                
        except Exception as e:
            logger.error(f"Error actualizando inventario: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene datos analíticos de la tienda"""
        try:
            # Datos básicos que podemos obtener directamente
            orders = await self._get_recent_orders(days)
            products = await self._get_popular_products(limit=100)
            
            # Calcular métricas
            total_revenue = sum(float(order.get("total_price", 0)) for order in orders)
            total_orders = len(orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Análisis por día
            daily_sales = {}
            for order in orders:
                date = order.get("created_at", "")[:10]  # Obtener solo la fecha
                if date not in daily_sales:
                    daily_sales[date] = {"revenue": 0, "orders": 0}
                daily_sales[date]["revenue"] += float(order.get("total_price", 0))
                daily_sales[date]["orders"] += 1
            
            return {
                "period_days": days,
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "average_order_value": average_order_value,
                "daily_breakdown": daily_sales,
                "total_products": len(products),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos analíticos: {e}")
            return {"error": str(e)}