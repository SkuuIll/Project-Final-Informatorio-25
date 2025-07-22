"""
Management command to monitor database performance and generate reports.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import time
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Monitor database performance and generate reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Monitoring duration in seconds (default: 60)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for the report (JSON format)'
        )
        parser.add_argument(
            '--slow-threshold',
            type=float,
            default=0.1,
            help='Slow query threshold in seconds (default: 0.1)'
        )
    
    def handle(self, *args, **options):
        duration = options['duration']
        output_file = options['output']
        slow_threshold = options['slow_threshold']
        
        self.stdout.write(f"Starting database monitoring for {duration} seconds...")
        
        # Initialize monitoring
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        # Monitor for specified duration
        time.sleep(duration)
        
        # Collect final metrics
        end_time = time.time()
        final_queries = len(connection.queries)
        
        # Analyze queries
        monitored_queries = connection.queries[initial_queries:final_queries]
        
        report = self._generate_report(
            monitored_queries, 
            start_time, 
            end_time, 
            slow_threshold
        )
        
        # Output report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.stdout.write(f"Report saved to {output_file}")
        else:
            self._print_report(report)
    
    def _generate_report(self, queries, start_time, end_time, slow_threshold):
        """Generate performance report from monitored queries."""
        total_time = end_time - start_time
        query_count = len(queries)
        
        if query_count == 0:
            return {
                'monitoring_duration': total_time,
                'total_queries': 0,
                'message': 'No queries executed during monitoring period'
            }
        
        # Calculate metrics
        query_times = [float(q['time']) for q in queries]
        total_query_time = sum(query_times)
        avg_query_time = total_query_time / query_count
        
        slow_queries = [q for q in queries if float(q['time']) > slow_threshold]
        
        # Analyze query patterns
        query_patterns = self._analyze_patterns(queries)
        
        # Database connection stats
        db_stats = self._get_db_stats()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_duration': total_time,
            'total_queries': query_count,
            'total_query_time': total_query_time,
            'average_query_time': avg_query_time,
            'queries_per_second': query_count / total_time,
            'slow_queries': {
                'count': len(slow_queries),
                'threshold': slow_threshold,
                'queries': [
                    {
                        'time': q['time'],
                        'sql': q['sql'][:200] + '...' if len(q['sql']) > 200 else q['sql']
                    }
                    for q in slow_queries[:10]  # Top 10 slow queries
                ]
            },
            'query_patterns': query_patterns,
            'database_stats': db_stats,
            'recommendations': self._generate_recommendations(
                query_count, len(slow_queries), query_patterns
            )
        }
        
        return report
    
    def _analyze_patterns(self, queries):
        """Analyze query patterns to detect potential issues."""
        patterns = {}
        
        for query in queries:
            # Normalize SQL
            normalized = self._normalize_sql(query['sql'])
            if normalized in patterns:
                patterns[normalized]['count'] += 1
                patterns[normalized]['total_time'] += float(query['time'])
            else:
                patterns[normalized] = {
                    'count': 1,
                    'total_time': float(query['time']),
                    'example': query['sql'][:100] + '...' if len(query['sql']) > 100 else query['sql']
                }
        
        # Sort by frequency
        sorted_patterns = sorted(
            patterns.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        return {
            pattern: {
                **data,
                'avg_time': data['total_time'] / data['count']
            }
            for pattern, data in sorted_patterns[:10]  # Top 10 patterns
        }
    
    def _normalize_sql(self, sql):
        """Normalize SQL for pattern analysis."""
        import re
        # Remove specific values
        normalized = re.sub(r'\b\d+\b', 'N', sql)
        normalized = re.sub(r"'[^']*'", "'VALUE'", normalized)
        normalized = re.sub(r'"[^"]*"', '"VALUE"', normalized)
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return normalized[:150]
    
    def _get_db_stats(self):
        """Get database connection statistics."""
        try:
            with connection.cursor() as cursor:
                # PostgreSQL specific queries
                cursor.execute("""
                    SELECT 
                        numbackends as active_connections,
                        xact_commit as transactions_committed,
                        xact_rollback as transactions_rolled_back,
                        blks_read as blocks_read,
                        blks_hit as blocks_hit,
                        tup_returned as tuples_returned,
                        tup_fetched as tuples_fetched,
                        tup_inserted as tuples_inserted,
                        tup_updated as tuples_updated,
                        tup_deleted as tuples_deleted
                    FROM pg_stat_database 
                    WHERE datname = current_database();
                """)
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
        except Exception as e:
            return {'error': str(e)}
        
        return {}
    
    def _generate_recommendations(self, query_count, slow_query_count, patterns):
        """Generate performance recommendations."""
        recommendations = []
        
        if slow_query_count > 0:
            recommendations.append(
                f"Found {slow_query_count} slow queries. Consider adding indexes or optimizing these queries."
            )
        
        # Check for potential N+1 problems
        high_frequency_patterns = [
            pattern for pattern, data in patterns.items() 
            if data['count'] > 10
        ]
        
        if high_frequency_patterns:
            recommendations.append(
                f"Found {len(high_frequency_patterns)} query patterns with high frequency. "
                "Consider using select_related() or prefetch_related() to reduce N+1 queries."
            )
        
        if query_count > 50:
            recommendations.append(
                "High query count detected. Consider implementing caching or query optimization."
            )
        
        if not recommendations:
            recommendations.append("Database performance looks good!")
        
        return recommendations
    
    def _print_report(self, report):
        """Print report to console."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("DATABASE PERFORMANCE REPORT")
        self.stdout.write("="*50)
        
        self.stdout.write(f"Monitoring Duration: {report['monitoring_duration']:.2f} seconds")
        self.stdout.write(f"Total Queries: {report['total_queries']}")
        self.stdout.write(f"Average Query Time: {report['average_query_time']:.4f} seconds")
        self.stdout.write(f"Queries per Second: {report['queries_per_second']:.2f}")
        
        if report['slow_queries']['count'] > 0:
            self.stdout.write(f"\nSlow Queries: {report['slow_queries']['count']}")
            for query in report['slow_queries']['queries'][:5]:
                self.stdout.write(f"  - {query['time']}s: {query['sql']}")
        
        self.stdout.write("\nTop Query Patterns:")
        for pattern, data in list(report['query_patterns'].items())[:5]:
            self.stdout.write(f"  - Count: {data['count']}, Avg Time: {data['avg_time']:.4f}s")
            self.stdout.write(f"    Example: {data['example']}")
        
        self.stdout.write("\nRecommendations:")
        for rec in report['recommendations']:
            self.stdout.write(f"  - {rec}")
        
        self.stdout.write("="*50)