"""
Management command to check database performance and connection pooling.
"""
import time
import json
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.conf import settings
from blog.query_monitoring import get_db_stats


class Command(BaseCommand):
    help = 'Check database performance and connection pooling'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queries',
            type=int,
            default=100,
            help='Number of test queries to run'
        )
        parser.add_argument(
            '--pgbouncer',
            action='store_true',
            help='Check pgbouncer status'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show database statistics'
        )
        parser.add_argument(
            '--slow-queries',
            action='store_true',
            help='Show slow queries from logs'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Database Performance Check'))
        
        # Show database configuration
        self.stdout.write(self.style.NOTICE('\nDatabase Configuration:'))
        for alias in connections:
            conn = connections[alias]
            self.stdout.write(f"- {alias}: {conn.settings_dict.get('ENGINE')} - {conn.settings_dict.get('NAME')}")
            self.stdout.write(f"  Host: {conn.settings_dict.get('HOST')}:{conn.settings_dict.get('PORT')}")
            self.stdout.write(f"  CONN_MAX_AGE: {conn.settings_dict.get('CONN_MAX_AGE')}")
            
            if 'OPTIONS' in conn.settings_dict:
                self.stdout.write(f"  OPTIONS: {json.dumps(conn.settings_dict['OPTIONS'], indent=2)}")
        
        # Check pgbouncer status if requested
        if options['pgbouncer']:
            self.check_pgbouncer()
        
        # Show database statistics if requested
        if options['stats']:
            self.show_db_stats()
        
        # Show slow queries if requested
        if options['slow_queries']:
            self.show_slow_queries()
        
        # Run performance test
        self.run_performance_test(options['queries'])
    
    def check_pgbouncer(self):
        """Check pgbouncer status"""
        self.stdout.write(self.style.NOTICE('\nPgBouncer Status:'))
        
        try:
            # Check if pgbouncer is enabled in settings
            pgbouncer_enabled = getattr(settings, 'USE_PGBOUNCER', False)
            self.stdout.write(f"PgBouncer enabled in settings: {pgbouncer_enabled}")
            
            # Try to connect to pgbouncer and get stats
            with connection.cursor() as cursor:
                try:
                    # This will only work if connected through pgbouncer
                    cursor.execute("SHOW POOLS")
                    pools = cursor.fetchall()
                    self.stdout.write(self.style.SUCCESS(f"Connected to PgBouncer: {len(pools)} pools found"))
                    
                    # Show pool details
                    for pool in pools:
                        self.stdout.write(f"- Pool: {pool}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Not connected through PgBouncer: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking PgBouncer: {str(e)}"))
    
    def show_db_stats(self):
        """Show database statistics"""
        self.stdout.write(self.style.NOTICE('\nDatabase Statistics:'))
        
        stats = get_db_stats()
        for alias, db_stats in stats.items():
            self.stdout.write(f"\nDatabase: {alias}")
            
            # Basic connection info
            self.stdout.write(f"- Vendor: {db_stats.get('vendor')}")
            self.stdout.write(f"- Is usable: {db_stats.get('is_usable')}")
            
            # PostgreSQL specific stats
            if 'database_size' in db_stats:
                self.stdout.write(f"- Database size: {db_stats.get('database_size')}")
            
            if 'active_connections' in db_stats:
                self.stdout.write(f"- Active connections: {db_stats.get('active_connections')}")
            
            # Table statistics
            if 'table_stats' in db_stats and db_stats['table_stats']:
                self.stdout.write("\nTop tables by row count:")
                for table in db_stats['table_stats']:
                    self.stdout.write(f"- {table['table']}: {table['live_rows']} live rows, {table['dead_rows']} dead rows")
    
    def show_slow_queries(self):
        """Show slow queries from logs"""
        self.stdout.write(self.style.NOTICE('\nSlow Queries:'))
        
        try:
            # Try to read slow queries log file
            log_file = settings.LOGGING['handlers'].get('slow_queries', {}).get('filename')
            if log_file:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-20:]  # Get last 20 lines
                    
                    if not lines:
                        self.stdout.write("No slow queries found in log file.")
                    else:
                        for line in lines:
                            try:
                                data = json.loads(line)
                                self.stdout.write(f"- {data.get('message', '')}")
                                if 'query_sql' in data:
                                    self.stdout.write(f"  SQL: {data['query_sql'][:100]}...")
                                if 'query_time_ms' in data:
                                    self.stdout.write(f"  Time: {data['query_time_ms']}ms")
                                self.stdout.write("")
                            except json.JSONDecodeError:
                                self.stdout.write(f"- {line.strip()}")
            else:
                self.stdout.write(self.style.WARNING("Slow queries log file not configured."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading slow queries log: {str(e)}"))
    
    def run_performance_test(self, num_queries):
        """Run a simple performance test"""
        self.stdout.write(self.style.NOTICE(f'\nRunning Performance Test ({num_queries} queries):'))
        
        # Clear connection queries
        connection.queries_log.clear()
        
        # Run test queries
        start_time = time.time()
        
        for i in range(num_queries):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # ms
        
        # Calculate statistics
        avg_query_time = duration / num_queries
        
        self.stdout.write(self.style.SUCCESS(f"Completed {num_queries} queries in {duration:.2f}ms"))
        self.stdout.write(f"Average query time: {avg_query_time:.2f}ms")
        
        # Show connection pool info
        self.stdout.write("\nConnection pool status:")
        for alias in connections:
            conn = connections[alias]
            self.stdout.write(f"- {alias}: {'Connected' if conn.connection is not None else 'Not connected'}")