"""
Base de Datos Deportiva
Procesa y analiza información de equipos y partidos deportivos
"""

import os
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)

class SportsDatabase:
    """
    Maneja los datos deportivos privados (equipos y partidos)
    Proporciona análisis y contexto para el agente de IA
    """
    
    def __init__(self):
        self.teams = []
        self.games = []
        self.team_records = {}
        self.team_stats = {}
        self.last_updated = None
        
        # Paths a los archivos de datos
        self.teams_file = "equipos.txt"
        self.games_file = "partidos.txt"
    
    async def load_data(self):
        """Carga y procesa los datos deportivos"""
        try:
            await self._load_teams()
            await self._load_games()
            await self._calculate_team_stats()
            self.last_updated = datetime.now()
            logger.info(f"✅ Datos deportivos cargados: {len(self.teams)} equipos, {len(self.games)} partidos")
        except Exception as e:
            logger.error(f"❌ Error cargando datos deportivos: {e}")
            raise
    
    async def _load_teams(self):
        """Carga la lista de equipos desde el archivo"""
        try:
            if not os.path.exists(self.teams_file):
                logger.warning(f"Archivo de equipos no encontrado: {self.teams_file}")
                return
            
            with open(self.teams_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Los equipos están separados por comas
                self.teams = [team.strip() for team in content.split(',') if team.strip()]
            
            logger.info(f"Cargados {len(self.teams)} equipos")
            
        except Exception as e:
            logger.error(f"Error cargando equipos: {e}")
            raise
    
    async def _load_games(self):
        """Carga y procesa los datos de partidos"""
        try:
            if not os.path.exists(self.games_file):
                logger.warning(f"Archivo de partidos no encontrado: {self.games_file}")
                return
            
            with open(self.games_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.games = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    game_data = self._parse_game_line(line)
                    if game_data:
                        self.games.append(game_data)
                except Exception as e:
                    logger.warning(f"Error procesando línea {line_num}: {line} - {e}")
            
            logger.info(f"Cargados {len(self.games)} partidos")
            
        except Exception as e:
            logger.error(f"Error cargando partidos: {e}")
            raise
    
    def _parse_game_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parsea una línea de partido con formato:
        Team1,Score1,vs/at,Team2,Score2
        """
        try:
            parts = [part.strip() for part in line.split(',')]
            if len(parts) != 5:
                return None
            
            team1, score1, location, team2, score2 = parts
            
            # Convertir scores a enteros
            score1 = int(score1)
            score2 = int(score2)
            
            # Determinar ganador
            winner = team1 if score1 > score2 else team2
            loser = team2 if score1 > score2 else team1
            winner_score = max(score1, score2)
            loser_score = min(score1, score2)
            
            # Determinar si es juego en casa o fuera
            team1_home = location == "vs"
            
            return {
                "team1": team1,
                "team2": team2,
                "score1": score1,
                "score2": score2,
                "location": location,
                "team1_home": team1_home,
                "winner": winner,
                "loser": loser,
                "winner_score": winner_score,
                "loser_score": loser_score,
                "margin": winner_score - loser_score,
                "total_points": score1 + score2,
                "close_game": abs(score1 - score2) <= 7,
                "blowout": abs(score1 - score2) >= 21
            }
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parseando línea de juego: {line} - {e}")
            return None
    
    async def _calculate_team_stats(self):
        """Calcula estadísticas completas para todos los equipos"""
        try:
            self.team_records = {}
            self.team_stats = {}
            
            for team in self.teams:
                self.team_records[team] = {
                    "wins": 0,
                    "losses": 0,
                    "games_played": 0,
                    "points_for": 0,
                    "points_against": 0,
                    "home_wins": 0,
                    "home_losses": 0,
                    "away_wins": 0,
                    "away_losses": 0,
                    "close_games": 0,
                    "blowout_wins": 0,
                    "blowout_losses": 0
                }
            
            # Procesar cada juego
            for game in self.games:
                team1, team2 = game["team1"], game["team2"]
                winner, loser = game["winner"], game["loser"]
                
                # Actualizar records básicos
                if team1 in self.team_records:
                    self.team_records[team1]["games_played"] += 1
                    self.team_records[team1]["points_for"] += game["score1"]
                    self.team_records[team1]["points_against"] += game["score2"]
                    
                    if winner == team1:
                        self.team_records[team1]["wins"] += 1
                        if game["team1_home"]:
                            self.team_records[team1]["home_wins"] += 1
                        else:
                            self.team_records[team1]["away_wins"] += 1
                        
                        if game["blowout"]:
                            self.team_records[team1]["blowout_wins"] += 1
                    else:
                        self.team_records[team1]["losses"] += 1
                        if game["team1_home"]:
                            self.team_records[team1]["home_losses"] += 1
                        else:
                            self.team_records[team1]["away_losses"] += 1
                        
                        if game["blowout"]:
                            self.team_records[team1]["blowout_losses"] += 1
                    
                    if game["close_game"]:
                        self.team_records[team1]["close_games"] += 1
                
                # Hacer lo mismo para team2
                if team2 in self.team_records:
                    self.team_records[team2]["games_played"] += 1
                    self.team_records[team2]["points_for"] += game["score2"]
                    self.team_records[team2]["points_against"] += game["score1"]
                    
                    if winner == team2:
                        self.team_records[team2]["wins"] += 1
                        if not game["team1_home"]:  # team2 está en casa
                            self.team_records[team2]["home_wins"] += 1
                        else:
                            self.team_records[team2]["away_wins"] += 1
                        
                        if game["blowout"]:
                            self.team_records[team2]["blowout_wins"] += 1
                    else:
                        self.team_records[team2]["losses"] += 1
                        if not game["team1_home"]:
                            self.team_records[team2]["home_losses"] += 1
                        else:
                            self.team_records[team2]["away_losses"] += 1
                        
                        if game["blowout"]:
                            self.team_records[team2]["blowout_losses"] += 1
                    
                    if game["close_game"]:
                        self.team_records[team2]["close_games"] += 1
            
            # Calcular estadísticas avanzadas
            await self._calculate_advanced_stats()
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
            raise
    
    async def _calculate_advanced_stats(self):
        """Calcula estadísticas avanzadas para cada equipo"""
        for team, record in self.team_records.items():
            games_played = record["games_played"]
            if games_played == 0:
                continue
            
            wins = record["wins"]
            losses = record["losses"]
            points_for = record["points_for"]
            points_against = record["points_against"]
            
            # Estadísticas básicas
            win_percentage = wins / games_played if games_played > 0 else 0
            avg_points_for = points_for / games_played
            avg_points_against = points_against / games_played
            point_differential = avg_points_for - avg_points_against
            
            # Estadísticas de local/visitante
            home_games = record["home_wins"] + record["home_losses"]
            away_games = record["away_wins"] + record["away_losses"]
            home_win_pct = record["home_wins"] / home_games if home_games > 0 else 0
            away_win_pct = record["away_wins"] / away_games if away_games > 0 else 0
            
            # Rendimiento en juegos cerrados
            close_game_performance = record["close_games"] / games_played if games_played > 0 else 0
            
            self.team_stats[team] = {
                "record": f"{wins}-{losses}",
                "win_percentage": round(win_percentage, 3),
                "avg_points_for": round(avg_points_for, 1),
                "avg_points_against": round(avg_points_against, 1),
                "point_differential": round(point_differential, 1),
                "home_record": f"{record['home_wins']}-{record['home_losses']}",
                "away_record": f"{record['away_wins']}-{record['away_losses']}",
                "home_win_percentage": round(home_win_pct, 3),
                "away_win_percentage": round(away_win_pct, 3),
                "close_games_played": record["close_games"],
                "close_game_rate": round(close_game_performance, 3),
                "blowout_wins": record["blowout_wins"],
                "blowout_losses": record["blowout_losses"],
                "games_played": games_played
            }
    
    async def get_all_teams(self) -> List[str]:
        """Obtiene lista de todos los equipos"""
        return self.teams.copy()
    
    async def get_team_info(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información completa de un equipo"""
        if team_name not in self.team_stats:
            # Buscar por nombre parcial
            matches = [team for team in self.teams if team_name.lower() in team.lower()]
            if matches:
                team_name = matches[0]
            else:
                return None
        
        team_record = self.team_records.get(team_name, {})
        team_stats = self.team_stats.get(team_name, {})
        recent_games = await self._get_team_recent_games(team_name, limit=5)
        
        return {
            "name": team_name,
            "record": team_stats.get("record", "0-0"),
            "win_percentage": team_stats.get("win_percentage", 0),
            "stats": team_stats,
            "recent_games": recent_games,
            "recent_performance": await self._analyze_recent_performance(team_name),
            "strengths": await self._identify_team_strengths(team_name),
            "trends": await self._analyze_team_trends(team_name)
        }
    
    async def _get_team_recent_games(self, team_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los juegos más recientes de un equipo"""
        team_games = []
        
        for game in self.games:
            if team_name in [game["team1"], game["team2"]]:
                # Determinar si ganó o perdió
                team_won = game["winner"] == team_name
                team_score = game["score1"] if game["team1"] == team_name else game["score2"]
                opponent_score = game["score2"] if game["team1"] == team_name else game["score1"]
                opponent = game["team2"] if game["team1"] == team_name else game["team1"]
                
                # Determinar si jugó en casa
                if game["team1"] == team_name:
                    location = "vs" if game["location"] == "vs" else "at"
                else:
                    location = "vs" if game["location"] == "at" else "at"
                
                game_summary = {
                    "opponent": opponent,
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "result": "W" if team_won else "L",
                    "location": location,
                    "margin": abs(team_score - opponent_score),
                    "close_game": game["close_game"],
                    "blowout": game["blowout"]
                }
                team_games.append(game_summary)
        
        # Retornar los últimos juegos (asumiendo que están en orden cronológico)
        return team_games[-limit:] if team_games else []
    
    async def _analyze_recent_performance(self, team_name: str) -> Dict[str, Any]:
        """Analiza el rendimiento reciente de un equipo"""
        recent_games = await self._get_team_recent_games(team_name, limit=5)
        
        if not recent_games:
            return {"status": "no_data"}
        
        wins = sum(1 for game in recent_games if game["result"] == "W")
        losses = len(recent_games) - wins
        
        # Calcular tendencia
        if wins >= 4:
            trend = "hot"
        elif wins >= 3:
            trend = "good"
        elif wins == 2:
            trend = "average"
        elif wins == 1:
            trend = "struggling"
        else:
            trend = "cold"
        
        return {
            "recent_record": f"{wins}-{losses}",
            "trend": trend,
            "momentum": "positive" if wins > losses else "negative" if losses > wins else "neutral",
            "avg_margin": round(sum(game["margin"] for game in recent_games) / len(recent_games), 1),
            "close_games": sum(1 for game in recent_games if game["close_game"]),
            "blowouts": sum(1 for game in recent_games if game["blowout"])
        }
    
    async def _identify_team_strengths(self, team_name: str) -> List[str]:
        """Identifica las fortalezas de un equipo"""
        if team_name not in self.team_stats:
            return []
        
        stats = self.team_stats[team_name]
        strengths = []
        
        # Análisis de rendimiento
        if stats["win_percentage"] >= 0.750:
            strengths.append("Equipo dominante con excelente record")
        elif stats["win_percentage"] >= 0.600:
            strengths.append("Equipo sólido con buen record")
        
        # Análisis ofensivo/defensivo
        if stats["point_differential"] >= 10:
            strengths.append("Excelente diferencia de puntos")
        elif stats["point_differential"] >= 5:
            strengths.append("Buena diferencia de puntos")
        
        if stats["avg_points_for"] >= 35:
            strengths.append("Ofensiva explosiva")
        elif stats["avg_points_for"] >= 28:
            strengths.append("Buena ofensiva")
        
        if stats["avg_points_against"] <= 14:
            strengths.append("Defensiva dominante")
        elif stats["avg_points_against"] <= 21:
            strengths.append("Defensiva sólida")
        
        # Análisis de local/visitante
        if stats["home_win_percentage"] >= 0.800:
            strengths.append("Muy fuerte jugando en casa")
        
        if stats["away_win_percentage"] >= 0.600:
            strengths.append("Buen rendimiento como visitante")
        
        # Análisis de juegos cerrados
        if stats["close_game_rate"] >= 0.4 and stats["win_percentage"] >= 0.600:
            strengths.append("Fuerte en juegos cerrados")
        
        return strengths
    
    async def _analyze_team_trends(self, team_name: str) -> Dict[str, Any]:
        """Analiza tendencias del equipo"""
        recent_performance = await self._analyze_recent_performance(team_name)
        
        if team_name not in self.team_stats:
            return {"status": "no_data"}
        
        stats = self.team_stats[team_name]
        
        # Análisis de momentum
        momentum_factors = []
        
        if recent_performance["trend"] in ["hot", "good"]:
            momentum_factors.append("Racha ganadora reciente")
        elif recent_performance["trend"] in ["struggling", "cold"]:
            momentum_factors.append("Atravesando dificultades")
        
        # Análisis de consistencia
        consistency_score = 1.0 - (stats["close_game_rate"] * 0.5)  # Menos juegos cerrados = más consistencia
        
        if consistency_score >= 0.8:
            momentum_factors.append("Muy consistente")
        elif consistency_score >= 0.6:
            momentum_factors.append("Moderadamente consistente")
        else:
            momentum_factors.append("Inconsistente")
        
        return {
            "momentum_direction": recent_performance["momentum"],
            "consistency_level": consistency_score,
            "factors": momentum_factors,
            "outlook": self._generate_outlook(stats, recent_performance)
        }
    
    def _generate_outlook(self, stats: Dict[str, Any], recent_performance: Dict[str, Any]) -> str:
        """Genera una perspectiva sobre el equipo"""
        if stats["win_percentage"] >= 0.750 and recent_performance["trend"] in ["hot", "good"]:
            return "Excelente - Equipo top con momentum positivo"
        elif stats["win_percentage"] >= 0.600:
            if recent_performance["trend"] in ["hot", "good"]:
                return "Muy bueno - Equipo sólido en buena racha"
            else:
                return "Bueno - Equipo sólido pero necesita retomar momentum"
        elif stats["win_percentage"] >= 0.400:
            if recent_performance["trend"] in ["hot", "good"]:
                return "Promedio+ - Mostrando mejoras recientes"
            else:
                return "Promedio - Rendimiento inconsistente"
        else:
            if recent_performance["trend"] in ["hot", "good"]:
                return "En desarrollo - Signos de mejora"
            else:
                return "Difícil - Necesita cambios significativos"
    
    async def get_relevant_context(self, message: str) -> Dict[str, Any]:
        """
        Obtiene contexto deportivo relevante basado en un mensaje
        """
        try:
            relevant_teams = []
            mentioned_teams = []
            
            # Buscar equipos mencionados en el mensaje
            message_lower = message.lower()
            for team in self.teams:
                if team.lower() in message_lower:
                    mentioned_teams.append(team)
                    team_info = await self.get_team_info(team)
                    if team_info:
                        relevant_teams.append(team_info)
            
            # Si no se mencionan equipos específicos, buscar por palabras clave
            if not relevant_teams:
                keywords = ["winning", "ganador", "mejor", "top", "ranking"]
                if any(keyword in message_lower for keyword in keywords):
                    # Obtener equipos top por win percentage
                    top_teams = sorted(
                        [(team, stats["win_percentage"]) for team, stats in self.team_stats.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:3]
                    
                    for team, _ in top_teams:
                        team_info = await self.get_team_info(team)
                        if team_info:
                            relevant_teams.append(team_info)
            
            # Obtener juegos recientes relevantes
            recent_games = []
            if mentioned_teams:
                for team in mentioned_teams:
                    team_games = await self._get_team_recent_games(team, limit=3)
                    for game in team_games:
                        recent_games.append(f"{team} {game['result']} {game['location']} {game['opponent']} {game['team_score']}-{game['opponent_score']}")
            
            return {
                "relevant_teams": relevant_teams,
                "mentioned_teams": mentioned_teams,
                "recent_games": recent_games,
                "context_quality": "high" if mentioned_teams else "general"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto relevante: {e}")
            return {"error": str(e)}
    
    async def get_team_results(self, team_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtiene resultados recientes de un equipo para análisis de correlación
        """
        try:
            team_info = await self.get_team_info(team_name)
            if not team_info:
                return {"error": "Equipo no encontrado"}
            
            recent_games = await self._get_team_recent_games(team_name, limit=10)
            recent_performance = await self._analyze_recent_performance(team_name)
            
            return {
                "team_name": team_name,
                "record": team_info["record"],
                "recent_games": recent_games,
                "recent_performance": recent_performance,
                "win_percentage": team_info["stats"]["win_percentage"],
                "avg_margin": team_info["stats"]["point_differential"],
                "strengths": team_info["strengths"],
                "trends": team_info["trends"]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resultados del equipo {team_name}: {e}")
            return {"error": str(e)}
    
    async def get_detailed_performance(self, team_name: str, season: str = "current") -> Dict[str, Any]:
        """Obtiene rendimiento detallado de un equipo"""
        try:
            team_info = await self.get_team_info(team_name)
            if not team_info:
                return {"error": "Equipo no encontrado"}
            
            # Obtener todos los juegos del equipo
            all_games = []
            for game in self.games:
                if team_name in [game["team1"], game["team2"]]:
                    all_games.append(game)
            
            # Análisis de oponentes
            opponents = []
            for game in all_games:
                opponent = game["team2"] if game["team1"] == team_name else game["team1"]
                opponents.append(opponent)
            
            opponent_analysis = Counter(opponents)
            
            return {
                "team_name": team_name,
                "overall_record": team_info["record"],
                "detailed_stats": team_info["stats"],
                "total_games": len(all_games),
                "opponents_faced": len(set(opponents)),
                "most_common_opponents": dict(opponent_analysis.most_common(5)),
                "recent_performance": team_info["recent_performance"],
                "strengths": team_info["strengths"],
                "trends": team_info["trends"],
                "season": season
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo rendimiento detallado: {e}")
            return {"error": str(e)}
    
    async def get_last_update(self) -> str:
        """Obtiene la fecha de última actualización"""
        if self.last_updated:
            return self.last_updated.isoformat()
        return "No actualizado"
    
    async def search_teams_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca equipos que cumplan ciertos criterios"""
        try:
            results = []
            
            min_win_pct = criteria.get("min_win_percentage", 0.0)
            max_win_pct = criteria.get("max_win_percentage", 1.0)
            min_points = criteria.get("min_avg_points", 0)
            region = criteria.get("region")  # Podría implementarse basado en nombres
            
            for team_name, stats in self.team_stats.items():
                # Filtrar por win percentage
                if not (min_win_pct <= stats["win_percentage"] <= max_win_pct):
                    continue
                
                # Filtrar por puntos promedio
                if stats["avg_points_for"] < min_points:
                    continue
                
                # Obtener información completa del equipo
                team_info = await self.get_team_info(team_name)
                if team_info:
                    results.append(team_info)
            
            # Ordenar por win percentage
            results.sort(key=lambda x: x["stats"]["win_percentage"], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error buscando equipos por criterios: {e}")
            return []