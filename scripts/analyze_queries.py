#!/usr/bin/env python
"""
Script para analizar logs de consultas SQL y detectar problemas de rendimiento.
"""
import re
import sys
import json
import argparse
from collections import defaultdict
from datetime import datetime

# Patrones para extraer información de logs
QUERY_PATTERN = re.compile(r'\[SQL\] \((\d+\.\d+)s\) (.+)')
SLOW_QUERY_PATTERN = re.compile(r'Consultas lentas detectadas.*\[(\d+)\] (\d+\.\d+)s: (.+)')

def parse_log_file(log_file):
    """Parsea un archivo de log y extrae información de consultas SQL."""
    queries = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Intentar parsear como JSON si está en formato JSON
            try:
                log_entry = json.loads(line)
                if 'sql' in log_entry and 'time' in log_entry:
                    queries.append({
                        'sql': log_entry['sql'],
                        'time': float(log_entry['time']),
                        'timestamp': log_entry.get('timestamp', None)
                    })
                    continue
            except json.JSONDecodeError:
                pass
            
            # Intentar parsear con regex para formatos de texto
            match = QUERY_PATTERN.search(line)
            if match:
                time_str, sql = match.groups()
                queries.append({
                    'sql': sql,
                    'time': float(time_str),
                    'timestamp': None
                })
                continue
                
            match = SLOW_QUERY_PATTERN.search(line)
            if match:
                _, time_str, sql = match.groups()
                queries.append({
                    'sql': sql,
                    'time': float(time_str),
                    'timestamp': None
                })
    
    return queries

def normalize_query(sql):
    """Normaliza una consulta SQL para agrupar consultas similares."""
    # Reemplazar valores literales con placeholders
    sql = re.sub(r"'[^']*'", "'?'", sql)
    sql = re.sub(r"\d+", "?", sql)
    return sql

def analyze_queries(queries, slow_threshold=0.1):
    """Analiza las consultas y genera estadísticas."""
    total_queries = len(queries)
    total_time = sum(q['time'] for q in queries)
    slow_queries = [q for q in queries if q['time'] > slow_threshold]
    
    # Agrupar consultas similares
    query_groups = defaultdict(list)
    for query in queries:
        normalized = normalize_query(query['sql'])
        query_groups[normalized].append(query)
    
    # Calcular estadísticas por grupo
    query_stats = []
    for normalized, group in query_groups.items():
        count = len(group)
        total_group_time = sum(q['time'] for q in group)
        avg_time = total_group_time / count
        max_time = max(q['time'] for q in group)
        
        query_stats.append({
            'normalized_sql': normalized,
            'count': count,
            'total_time': total_group_time,
            'avg_time': avg_time,
            'max_time': max_time,
            'example': group[0]['sql']
        })
    
    # Ordenar por tiempo total
    query_stats.sort(key=lambda x: x['total_time'], reverse=True)
    
    return {
        'total_queries': total_queries,
        'total_time': total_time,
        'avg_time': total_time / total_queries if total_queries else 0,
        'slow_queries_count': len(slow_queries),
        'slow_queries_percent': (len(slow_queries) / total_queries * 100) if total_queries else 0,
        'query_stats': query_stats
    }

def print_report(stats):
    """Imprime un reporte de análisis de consultas."""
    print("\n===== REPORTE DE ANÁLISIS DE CONSULTAS SQL =====")
    print(f"Total de consultas: {stats['total_queries']}")
    print(f"Tiempo total: {stats['total_time']:.2f}s")
    print(f"Tiempo promedio: {stats['avg_time'] * 1000:.2f}ms")
    print(f"Consultas lentas: {stats['slow_queries_count']} ({stats['slow_queries_percent']:.1f}%)")
    
    print("\n----- TOP 10 CONSULTAS MÁS COSTOSAS -----")
    for i, stat in enumerate(stats['query_stats'][:10], 1):
        print(f"\n{i}. Ejecutada {stat['count']} veces, tiempo total: {stat['total_time']:.2f}s, "
              f"promedio: {stat['avg_time'] * 1000:.2f}ms, máximo: {stat['max_time'] * 1000:.2f}ms")
        print(f"Ejemplo: {stat['example'][:100]}...")
    
    print("\n----- RECOMENDACIONES -----")
    if stats['slow_queries_count'] > 0:
        print("- Revisar consultas lentas y optimizar con índices apropiados")
    
    n_plus_one_candidates = [s for s in stats['query_stats'] if s['count'] > 10 and s['avg_time'] < 0.01]
    if n_plus_one_candidates:
        print("- Posibles problemas N+1 detectados (muchas consultas pequeñas similares):")
        for i, stat in enumerate(n_plus_one_candidates[:3], 1):
            print(f"  {i}. Ejecutada {stat['count']} veces: {stat['example'][:80]}...")
        print("  Considerar usar select_related/prefetch_related o optimizar con joins")

def main():
    parser = argparse.ArgumentParser(description='Analiza logs de consultas SQL')
    parser.add_argument('log_file', help='Archivo de log a analizar')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='Umbral para consultas lentas en segundos (default: 0.1)')
    args = parser.parse_args()
    
    try:
        queries = parse_log_file(args.log_file)
        if not queries:
            print(f"No se encontraron consultas SQL en {args.log_file}")
            return 1
            
        stats = analyze_queries(queries, args.threshold)
        print_report(stats)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())