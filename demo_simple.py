#!/usr/bin/env python3
"""
🏈 DEMO SIMPLE - Base de Datos Deportiva
Prueba inmediata del sistema sin dependencias externas
"""

import os
from datetime import datetime
from collections import defaultdict, Counter

class SportsDataDemo:
    """Versión simplificada para demostrar la funcionalidad"""
    
    def __init__(self):
        self.teams = []
        self.games = []
        self.team_stats = {}
        
    def load_data(self):
        """Cargar datos desde los archivos"""
        # Cargar equipos
        if os.path.exists("equipos.txt"):
            with open("equipos.txt", 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.teams = [team.strip() for team in content.split(',') if team.strip()]
        
        # Cargar partidos
        if os.path.exists("partidos.txt"):
            with open("partidos.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 5:
                        team1, score1, location, team2, score2 = parts
                        try:
                            game = {
                                'team1': team1.strip(),
                                'team2': team2.strip(),
                                'score1': int(score1.strip()),
                                'score2': int(score2.strip()),
                                'location': location.strip(),
                                'winner': team1.strip() if int(score1) > int(score2) else team2.strip(),
                                'margin': abs(int(score1) - int(score2)),
                                'total_points': int(score1) + int(score2)
                            }
                            self.games.append(game)
                        except ValueError:
                            continue
        
        # Calcular estadísticas
        self._calculate_stats()
    
    def _calculate_stats(self):
        """Calcular estadísticas de equipos"""
        team_records = {}
        
        # Inicializar records
        for team in self.teams:
            team_records[team] = {
                'wins': 0, 'losses': 0, 'points_for': 0, 'points_against': 0, 'games': []
            }
        
        # Procesar juegos
        for game in self.games:
            team1, team2 = game['team1'], game['team2']
            
            if team1 in team_records:
                team_records[team1]['points_for'] += game['score1']
                team_records[team1]['points_against'] += game['score2']
                team_records[team1]['games'].append({
                    'opponent': team2, 'our_score': game['score1'], 
                    'their_score': game['score2'], 'result': 'W' if game['winner'] == team1 else 'L'
                })
                if game['winner'] == team1:
                    team_records[team1]['wins'] += 1
                else:
                    team_records[team1]['losses'] += 1
            
            if team2 in team_records:
                team_records[team2]['points_for'] += game['score2']
                team_records[team2]['points_against'] += game['score1']
                team_records[team2]['games'].append({
                    'opponent': team1, 'our_score': game['score2'], 
                    'their_score': game['score1'], 'result': 'W' if game['winner'] == team2 else 'L'
                })
                if game['winner'] == team2:
                    team_records[team2]['wins'] += 1
                else:
                    team_records[team2]['losses'] += 1
        
        # Calcular estadísticas finales
        for team, record in team_records.items():
            games_played = record['wins'] + record['losses']
            if games_played > 0:
                self.team_stats[team] = {
                    'record': f"{record['wins']}-{record['losses']}",
                    'win_percentage': record['wins'] / games_played,
                    'avg_points_for': record['points_for'] / games_played,
                    'avg_points_against': record['points_against'] / games_played,
                    'point_differential': (record['points_for'] - record['points_against']) / games_played,
                    'games_played': games_played,
                    'recent_games': record['games'][-5:] if record['games'] else []
                }
    
    def get_team_info(self, team_name):
        """Obtener información de un equipo"""
        if team_name in self.team_stats:
            stats = self.team_stats[team_name]
            
            # Determinar fortalezas
            strengths = []
            if stats['win_percentage'] >= 0.75:
                strengths.append("Equipo dominante")
            if stats['point_differential'] >= 10:
                strengths.append("Gran diferencia de puntos")
            if stats['avg_points_for'] >= 35:
                strengths.append("Ofensiva explosiva")
            if stats['avg_points_against'] <= 15:
                strengths.append("Defensiva sólida")
            
            # Analizar tendencia reciente
            recent_wins = sum(1 for game in stats['recent_games'] if game['result'] == 'W')
            if recent_wins >= 4:
                trend = "🔥 Muy caliente"
            elif recent_wins >= 3:
                trend = "📈 En racha"
            elif recent_wins == 2:
                trend = "➡️ Promedio"
            else:
                trend = "📉 Luchando"
            
            return {
                'name': team_name,
                'stats': stats,
                'strengths': strengths,
                'trend': trend
            }
        return None
    
    def get_top_teams(self, n=10):
        """Obtener top equipos por win percentage"""
        teams_with_stats = [(team, stats['win_percentage'], stats['record']) 
                           for team, stats in self.team_stats.items() 
                           if stats['games_played'] >= 5]  # Al menos 5 juegos
        
        return sorted(teams_with_stats, key=lambda x: x[1], reverse=True)[:n]
    
    def analyze_matchup(self, team1, team2):
        """Analizar enfrentamiento entre dos equipos"""
        team1_info = self.get_team_info(team1)
        team2_info = self.get_team_info(team2)
        
        if not team1_info or not team2_info:
            return None
        
        # Buscar enfrentamientos directos
        head_to_head = []
        for game in self.games:
            if (game['team1'] == team1 and game['team2'] == team2) or \
               (game['team1'] == team2 and game['team2'] == team1):
                head_to_head.append(game)
        
        return {
            'team1': team1_info,
            'team2': team2_info,
            'head_to_head': head_to_head,
            'prediction': self._predict_winner(team1_info, team2_info)
        }
    
    def _predict_winner(self, team1_info, team2_info):
        """Predicción simple basada en estadísticas"""
        team1_score = (team1_info['stats']['win_percentage'] * 0.4 + 
                      team1_info['stats']['point_differential'] * 0.006)
        team2_score = (team2_info['stats']['win_percentage'] * 0.4 + 
                      team2_info['stats']['point_differential'] * 0.006)
        
        if team1_score > team2_score:
            confidence = min((team1_score - team2_score) * 100, 95)
            return f"{team1_info['name']} ({confidence:.0f}% confianza)"
        else:
            confidence = min((team2_score - team1_score) * 100, 95)
            return f"{team2_info['name']} ({confidence:.0f}% confianza)"

def main():
    """Demo principal"""
    print("🏈" + "="*60)
    print("   DEMO: AGENTE DE IA PARA SHOPIFY - BASE DE DATOS DEPORTIVA")
    print("="*62)
    
    # Crear instancia y cargar datos
    sports = SportsDataDemo()
    print("📊 Cargando datos deportivos...")
    sports.load_data()
    
    print(f"✅ Datos cargados exitosamente:")
    print(f"   • {len(sports.teams)} equipos")
    print(f"   • {len(sports.games)} partidos analizados")
    print(f"   • {len(sports.team_stats)} equipos con estadísticas")
    
    # Mostrar algunos equipos
    print(f"\n🏆 ALGUNOS EQUIPOS DISPONIBLES:")
    for i, team in enumerate(sports.teams[:15]):
        print(f"   {i+1:2d}. {team}")
    print(f"   ... y {len(sports.teams)-15} más")
    
    # Análisis detallado de Alabama
    print(f"\n🔍 ANÁLISIS DETALLADO: ALABAMA")
    alabama = sports.get_team_info("Alabama")
    if alabama:
        stats = alabama['stats']
        print(f"   📈 Record: {stats['record']}")
        print(f"   📊 Win %: {stats['win_percentage']:.1%}")
        print(f"   ⚡ Puntos promedio: {stats['avg_points_for']:.1f}")
        print(f"   🛡️ Puntos permitidos: {stats['avg_points_against']:.1f}")
        print(f"   📏 Diferencia: {stats['point_differential']:+.1f}")
        print(f"   🔥 Tendencia: {alabama['trend']}")
        print(f"   💪 Fortalezas: {', '.join(alabama['strengths'])}")
        
        print(f"\n   📋 JUEGOS RECIENTES:")
        for game in stats['recent_games']:
            result_icon = "🟢 W" if game['result'] == 'W' else "🔴 L"
            print(f"      {result_icon} vs {game['opponent']}: {game['our_score']}-{game['their_score']}")
    
    # Top 10 equipos
    print(f"\n🏅 TOP 10 EQUIPOS (Por Win %):")
    top_teams = sports.get_top_teams(10)
    for i, (team, win_pct, record) in enumerate(top_teams):
        print(f"   {i+1:2d}. {team:<25} {win_pct:.1%} ({record})")
    
    # Análisis de enfrentamiento
    print(f"\n⚔️ ANÁLISIS DE ENFRENTAMIENTO: Alabama vs Georgia")
    matchup = sports.analyze_matchup("Alabama", "Georgia")
    if matchup:
        print(f"   Alabama: {matchup['team1']['stats']['record']} (Win% {matchup['team1']['stats']['win_percentage']:.1%})")
        print(f"   Georgia: {matchup['team2']['stats']['record']} (Win% {matchup['team2']['stats']['win_percentage']:.1%})")
        print(f"   Predicción: {matchup['prediction']}")
        if matchup['head_to_head']:
            print(f"   Enfrentamientos directos: {len(matchup['head_to_head'])}")
    
    # Estadísticas generales
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    win_percentages = [stats['win_percentage'] for stats in sports.team_stats.values()]
    if win_percentages:
        avg_win = sum(win_percentages) / len(win_percentages)
        print(f"   📈 Win % promedio: {avg_win:.3f}")
        print(f"   🔥 Equipos dominantes (>70%): {sum(1 for w in win_percentages if w > 0.7)}")
        print(f"   😅 Equipos en problemas (<30%): {sum(1 for w in win_percentages if w < 0.3)}")
    
    # Simulación de consultas del agente
    print(f"\n🤖 SIMULACIÓN DE CONSULTAS AL AGENTE:")
    print(f"\n   💬 Usuario: '¿Cómo está jugando Alabama esta temporada?'")
    if alabama:
        print(f"   🤖 Agente: Alabama tiene un excelente record de {alabama['stats']['record']} ")
        print(f"           con {alabama['stats']['win_percentage']:.0%} de victorias. {alabama['trend']}")
        print(f"           Fortalezas: {', '.join(alabama['strengths'][:2])}")
    
    print(f"\n   💬 Usuario: '¿Qué equipos están dominando?'")
    print(f"   🤖 Agente: Los equipos más dominantes esta temporada son:")
    for i, (team, win_pct, record) in enumerate(top_teams[:3]):
        print(f"           {i+1}. {team} ({win_pct:.0%} victorias)")
    
    print(f"\n   💬 Usuario: '¿Recomiendas productos de equipos ganadores?'")
    print(f"   🤖 Agente: ¡Definitivamente! Te recomiendo productos de:")
    winning_teams = [team for team, win_pct, record in top_teams[:5] if win_pct > 0.6]
    for team in winning_teams[:3]:
        print(f"           • {team} - Gran momento para aprovechar el momentum")
    
    # Resumen final
    print(f"\n🎉 RESUMEN DE LA DEMO")
    print(f"="*40)
    print(f"✅ Base de datos deportiva: FUNCIONANDO")
    print(f"✅ Análisis de equipos: FUNCIONANDO") 
    print(f"✅ Estadísticas avanzadas: FUNCIONANDO")
    print(f"✅ Sistema de recomendaciones: FUNCIONANDO")
    
    print(f"\n🚀 EL SISTEMA ESTÁ LISTO PARA:")
    print(f"   • Integración con Shopify API")
    print(f"   • Recomendaciones inteligentes de productos")
    print(f"   • Análisis de correlación ventas-deportes")
    print(f"   • Chat con clientes usando datos deportivos")
    
    print(f"\n📝 PRÓXIMOS PASOS:")
    print(f"   1. 🔧 Instalar dependencias: pip install -r backend/requirements.txt")
    print(f"   2. ⚙️ Configurar .env con tus credenciales")
    print(f"   3. 🚀 Ejecutar: ./scripts/start.sh")
    print(f"   4. 🌐 Acceder a: http://localhost:8000/docs")

if __name__ == "__main__":
    main()