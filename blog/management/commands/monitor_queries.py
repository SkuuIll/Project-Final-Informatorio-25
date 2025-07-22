"""
Management command to monitor database queries.
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.backends.utils import CursorWrapper
from django.conf import settings

logger = logging.getLogger('django.db.backends')

class QueryMonitoringCursorWrapper(CursorWrapper):
    """
    A cursor wrapper that logs executed queries.
    """
    def execute(self, sql, params=None):
        start = time.time()
        try:
            return super().execute(sql, params)
        finally:
            stop = time.time()
            duration = (stop - start) * 1000  # Convert to milliseconds
            
            # Log slow queries
            slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100)
            if duration > slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {duration:.2f}ms - {sql[:200]}...",
                    extra={
                        'duration_ms': duration,
                        'sql': sql,
                        'params': params,
                    }
                )
            else:
                logger.debug(
                    f"Query executed in {duration:.2f}ms - {sql[:200]}...",
                    extra={
                        'duration_ms': duration,
                        'sql': sql,
                        'params': params,
                    }
                )

    def executemany(self, sql, param_list):
        start = time.time()
        try:
            return super().executemany(sql, param_list)
        finally:
            stop = time.time()
            duration = (stop - start) * 1000  # Convert to milliseconds
            
            # Log slow queries
            slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100)
            if duration > slow_query_threshold:
                logger.warning(
                    f"Slow executemany query detected: {duration:.2f}ms - {sql[:200]}...",
                    extra={
                        'duration_ms': duration,
                        'sql': sql,
                        'param_count': len(param_list) if param_list else 0,
                    }
                )
            else:
                logger.debug(
                    f"Executemany query executed in {duration:.2f}ms - {sql[:200]}...",
                    extra={
                        'duration_ms': duration,
                        'sql': sql,
                        'param_count': len(param_list) if param_list else 0,
                    }
                )


class Command(BaseCommand):
    help = 'Monitor database queries and log slow queries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=100,
            help='Threshold in milliseconds to consider a query as slow (default: 100ms)',
        )
        parser.add_argument(
            '--log-all',
            action='store_true',
            help='Log all queries, not just slow ones',
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration in seconds to monitor queries (default: 60s)',
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        log_all = options['log_all']
        duration = options['duration']
        
        self.stdout.write(self.style.SUCCESS(f'Starting query monitoring for {duration} seconds'))
        self.stdout.write(f'Slow query threshold: {threshold}ms')
        self.stdout.write(f'Logging all queries: {log_all}')
        
        # Store original cursor
        original_cursor = connection.cursor
        
        try:
            # Replace cursor with monitoring cursor
            def cursor_wrapper(*args, **kwargs):
                return QueryMonitoringCursorWrapper(original_cursor(*args, **kwargs))
            
            connection.cursor = cursor_wrapper
            
            # Monitor for specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0:  # Print status every 10 seconds
                    self.stdout.write(f'Monitoring... {elapsed}/{duration} seconds')
            
            self.stdout.write(self.style.SUCCESS('Query monitoring completed'))
            
        finally:
            # Restore original cursor
            connection.cursor = original_cursor