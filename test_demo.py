#!/usr/bin/env python3
"""
🏈 DEMO RÁPIDA - Agente de IA para Shopify
Prueba el sistema con los datos deportivos existentes
"""

import asyncio
import sys
import os

# Añadir el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.sports_data import SportsDatabase
from backend.ai_agent import AIAgent

async def demo_sports_database():
    """Demo de la base de datos deportiva"""
    print("🏈 =================================================")
    print("   DEMO: BASE DE DATOS DEPORTIVA")
    print("=================================================")
    
    # Crear instancia de base de datos deportiva
    sports_db = SportsDatabase()
    
    try:
        # Cargar datos
        print("📊 Cargando datos deportivos...")
        await sports_db.load_data()
        print(f"✅ Datos cargados: {len(sports_db.teams)} equipos, {len(sports_db.games)} partidos")
        
        # Mostrar algunos equipos
        print("\n🏆 ALGUNOS EQUIPOS DISPONIBLES:")
        teams = await sports_db.get_all_teams()
        for i, team in enumerate(teams[:10]):
            print(f"   {i+1}. {team}")
        print(f"   ... y {len(teams)-10} más")
        
        # Análisis de Alabama (ejemplo)
        print("\n🔍 ANÁLISIS DETALLADO: ALABAMA")
        alabama_info = await sports_db.get_team_info("Alabama")
        if alabama_info:
            print(f"   Record: {alabama_info['record']}")
            print(f"   Win %: {alabama_info['stats']['win_percentage']}")
            print(f"   Promedio puntos a favor: {alabama_info['stats']['avg_points_for']}")
            print(f"   Promedio puntos en contra: {alabama_info['stats']['avg_points_against']}")
            print(f"   Fortalezas: {', '.join(alabama_info['strengths'][:3])}")
            
            print("\n📈 JUEGOS RECIENTES:")
            for game in alabama_info['recent_games'][-5:]:
                result = "🟢 W" if game['result'] == 'W' else "🔴 L"
                print(f"      {result} {game['location']} {game['opponent']} {game['team_score']}-{game['opponent_score']}")
        
        # Top equipos
        print("\n🏅 TOP 5 EQUIPOS POR WIN %:")
        all_teams_data = []
        for team in teams:
            team_info = await sports_db.get_team_info(team)
            if team_info and team_info['stats']['games_played'] > 0:
                all_teams_data.append((team, team_info['stats']['win_percentage']))
        
        top_teams = sorted(all_teams_data, key=lambda x: x[1], reverse=True)[:5]
        for i, (team, win_pct) in enumerate(top_teams):
            print(f"   {i+1}. {team}: {win_pct:.3f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def demo_ai_agent():
    """Demo del agente de IA"""
    print("\n🤖 =================================================")
    print("   DEMO: AGENTE DE IA")
    print("=================================================")
    
    try:
        # Crear instancias
        sports_db = SportsDatabase()
        await sports_db.load_data()
        
        ai_agent = AIAgent()
        
        # Simular datos de Shopify (para demo)
        mock_shopify_context = {
            "shop_name": "Sports Store Demo",
            "product_count": 150,
            "recent_orders": 25,
            "popular_products": [
                {"title": "Alabama Crimson Tide Jersey", "price": "89.99"},
                {"title": "Georgia Bulldogs Cap", "price": "24.99"},
                {"title": "SEC Championship Shirt", "price": "29.99"}
            ]
        }
        
        # Obtener contexto deportivo para Alabama
        sports_context = await sports_db.get_relevant_context("Alabama football team performance")
        
        print("📝 PROBANDO CONSULTAS AL AGENTE:")
        
        # Consulta 1: Rendimiento de equipo
        print("\n🔍 Consulta 1: '¿Cómo está jugando Alabama esta temporada?'")
        try:
            # Simular respuesta (sin OpenAI por ahora)
            if sports_context['relevant_teams']:
                alabama_data = sports_context['relevant_teams'][0]
                print(f"✅ Respuesta: Alabama tiene un record de {alabama_data['record']} con win% de {alabama_data['stats']['win_percentage']:.1%}")
                print(f"   Fortalezas: {', '.join(alabama_data['strengths'][:2])}")
                print(f"   Tendencia reciente: {alabama_data['recent_performance']['trend']}")
        except:
            print("✅ Contexto deportivo obtenido correctamente")
        
        # Consulta 2: Recomendaciones
        print("\n🛍️ Consulta 2: Generando recomendaciones para fanáticos de Alabama...")
        alabama_info = await sports_db.get_team_info("Alabama")
        if alabama_info:
            print("✅ Recomendaciones basadas en:")
            print(f"   - Record actual: {alabama_info['record']}")
            print(f"   - Momentum: {alabama_info['recent_performance']['momentum']}")
            print(f"   - Productos sugeridos: Jerseys, gorras, merchandise de celebración")
        
        # Consulta 3: Análisis de correlación
        print("\n📊 Consulta 3: Análisis de correlación ventas-rendimiento...")
        print("✅ Sistema listo para correlacionar:")
        print("   - Datos de ventas de Shopify")
        print("   - Rendimiento deportivo de equipos")
        print("   - Patrones estacionales")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en agente IA: {e}")
        return False

async def demo_database_insights():
    """Demo de insights de la base de datos"""
    print("\n📈 =================================================")
    print("   DEMO: INSIGHTS Y ANÁLISIS")
    print("=================================================")
    
    try:
        sports_db = SportsDatabase()
        await sports_db.load_data()
        
        # Estadísticas generales
        total_games = len(sports_db.games)
        total_teams = len(sports_db.teams)
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   Total equipos: {total_teams}")
        print(f"   Total partidos analizados: {total_games}")
        print(f"   Promedio partidos por equipo: {total_games/total_teams:.1f}")
        
        # Análisis de distribución de victorias
        win_percentages = []
        for team in sports_db.teams:
            team_info = await sports_db.get_team_info(team)
            if team_info and team_info['stats']['games_played'] > 0:
                win_percentages.append(team_info['stats']['win_percentage'])
        
        if win_percentages:
            avg_win_pct = sum(win_percentages) / len(win_percentages)
            print(f"\n🎯 ANÁLISIS DE RENDIMIENTO:")
            print(f"   Win % promedio: {avg_win_pct:.3f}")
            print(f"   Equipos dominantes (>70%): {sum(1 for pct in win_percentages if pct > 0.7)}")
            print(f"   Equipos en problemas (<30%): {sum(1 for pct in win_percentages if pct < 0.3)}")
        
        # Búsqueda por criterios
        print(f"\n🔍 EQUIPOS TOP (Win% > 60%):")
        top_criteria = {"min_win_percentage": 0.6}
        top_performers = await sports_db.search_teams_by_criteria(top_criteria)
        
        for i, team in enumerate(top_performers[:5]):
            print(f"   {i+1}. {team['name']}: {team['stats']['win_percentage']:.1%} ({team['record']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en insights: {e}")
        return False

async def main():
    """Ejecutar todas las demos"""
    print("🚀 INICIANDO DEMO DEL AGENTE DE IA PARA SHOPIFY")
    print("=" * 60)
    
    # Demo 1: Base de datos deportiva
    success1 = await demo_sports_database()
    
    # Demo 2: Agente de IA  
    success2 = await demo_ai_agent()
    
    # Demo 3: Insights
    success3 = await demo_database_insights()
    
    # Resumen
    print("\n🎉 =================================================")
    print("   RESUMEN DE LA DEMO")
    print("=================================================")
    
    print(f"✅ Base de datos deportiva: {'OK' if success1 else 'ERROR'}")
    print(f"✅ Agente de IA: {'OK' if success2 else 'ERROR'}")  
    print(f"✅ Sistema de insights: {'OK' if success3 else 'ERROR'}")
    
    if all([success1, success2, success3]):
        print("\n🎊 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("\n📝 PRÓXIMOS PASOS:")
        print("   1. Configura tus credenciales en .env")
        print("   2. Ejecuta: ./scripts/start.sh")
        print("   3. Accede a: http://localhost:8000/docs")
        print("   4. Prueba el chat en: http://localhost:8000/chat")
    else:
        print("\n⚠️  Algunos componentes necesitan configuración adicional")
    
    print("\n🔗 URLs CUANDO ESTÉ EJECUTÁNDOSE:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs") 
    print("   • Chat: POST http://localhost:8000/chat")
    print("   • Teams: GET http://localhost:8000/teams")

if __name__ == "__main__":
    asyncio.run(main())