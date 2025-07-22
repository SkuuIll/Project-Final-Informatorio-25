"""
Query monitoring middleware for detecting slow queries and N+1 problems.
"""
import time
import logging
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('query_monitor')


class QueryMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database queries and log slow queries.
    Detects N+1 query problems and logs performance metrics.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1)  # 100ms
        self.n_plus_one_threshold = getattr(settings, 'N_PLUS_ONE_THRESHOLD', 10)
        super().__init__(get_response)
    
    def process_request(self, request):
        """Reset query tracking at the start of each request."""
        self.start_time = time.time()
        self.start_queries = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Log query statistics after request processing."""
        if not settings.DEBUG and not getattr(settings, 'ENABLE_QUERY_MONITORING', False):
            return response
            
        end_time = time.time()
        total_time = end_time - self.start_time
        
        # Calculate query metrics
        total_queries = len(connection.queries) - self.start_queries
        query_time = sum(float(query['time']) for query in connection.queries[self.start_queries:])
        
        # Log basic metrics
        logger.info(
            f"Request: {request.method} {request.path} | "
            f"Total time: {total_time:.3f}s | "
            f"Query count: {total_queries} | "
            f"Query time: {query_time:.3f}s"
        )
        
        # Check for slow queries
        slow_queries = [
            query for query in connection.queries[self.start_queries:]
            if float(query['time']) > self.slow_query_threshold
        ]
        
        if slow_queries:
            logger.warning(
                f"Slow queries detected ({len(slow_queries)} queries > {self.slow_query_threshold}s):"
            )
            for query in slow_queries:
                logger.warning(
                    f"Query time: {query['time']}s | SQL: {query['sql'][:200]}..."
                )
        
        # Check for potential N+1 problems
        if total_queries > self.n_plus_one_threshold:
            logger.warning(
                f"Potential N+1 query problem detected: {total_queries} queries in single request"
            )
            
            # Analyze query patterns
            similar_queries = self._analyze_query_patterns(connection.queries[self.start_queries:])
            if similar_queries:
                logger.warning(f"Similar query patterns found: {similar_queries}")
        
        return response
    
    def _analyze_query_patterns(self, queries):
        """Analyze queries to detect similar patterns that might indicate N+1 problems."""
        query_patterns = {}
        
        for query in queries:
            # Normalize SQL by removing specific values
            normalized_sql = self._normalize_sql(query['sql'])
            if normalized_sql in query_patterns:
                query_patterns[normalized_sql] += 1
            else:
                query_patterns[normalized_sql] = 1
        
        # Return patterns that appear more than 3 times
        return {pattern: count for pattern, count in query_patterns.items() if count > 3}
    
    def _normalize_sql(self, sql):
        """Normalize SQL query by removing specific values."""
        import re
        # Remove specific IDs and values
        normalized = re.sub(r'\b\d+\b', 'N', sql)
        normalized = re.sub(r"'[^']*'", "'VALUE'", normalized)
        normalized = re.sub(r'"[^"]*"', '"VALUE"', normalized)
        return normalized[:100]  # Truncate for grouping


class QueryCountMiddleware(MiddlewareMixin):
    """
    Simple middleware to add query count to response headers in development.
    """
    
    def process_response(self, request, response):
        if settings.DEBUG:
            query_count = len(connection.queries)
            response['X-DB-Query-Count'] = str(query_count)
            
            total_time = sum(float(q['time']) for q in connection.queries)
            response['X-DB-Query-Time'] = f"{total_time:.3f}"
        
        return response