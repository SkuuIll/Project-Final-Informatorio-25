# Database Monitoring and Connection Pooling

This document describes the database monitoring and connection pooling features implemented in the DevBlog project.

## Query Monitoring

The project includes comprehensive query monitoring to detect slow queries and N+1 problems.

### Features

- **Slow Query Detection**: Logs queries that take longer than the configured threshold (default: 100ms)
- **N+1 Query Detection**: Identifies potential N+1 query problems by monitoring the number of queries per request
- **Query Statistics**: Collects and logs statistics about database queries
- **Performance Monitoring**: Tracks overall database performance metrics

### Configuration

The query monitoring system can be configured in `settings.py`:

```python
# Query monitoring thresholds
SLOW_QUERY_THRESHOLD_MS = 100  # Threshold for slow queries in milliseconds
QUERY_COUNT_THRESHOLD = 20     # Threshold for detecting N+1 problems
MONITOR_DB_QUERIES = True      # Enable query monitoring in production
```

### Usage

#### Using the QueryMonitor Context Manager

```python
from blog.query_monitoring import QueryMonitor

def get_user_posts(user_id):
    with QueryMonitor("Get user posts"):
        # Code that executes database queries
        posts = Post.objects.filter(author_id=user_id)
        return posts
```

#### Using the query_monitor Decorator

```python
from blog.query_monitoring import query_monitor

@query_monitor("Get user comments")
def get_user_comments(user_id):
    return Comment.objects.filter(author_id=user_id)
```

### Logs

Query monitoring logs are stored in the following files:

- `logs/db_queries.log`: All database queries
- `logs/slow_queries.log`: Slow queries that exceed the threshold

## Connection Pooling with PgBouncer

The project uses PgBouncer for database connection pooling to improve performance and resource utilization.

### Features

- **Connection Pooling**: Reuses database connections to reduce overhead
- **Connection Limits**: Controls the maximum number of connections to the database
- **Transaction Pooling**: Uses transaction-level pooling for optimal performance
- **Automatic Failover**: Handles database connection failures gracefully

### Configuration

PgBouncer can be configured using environment variables:

```
USE_PGBOUNCER=True
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432
PGBOUNCER_MAX_CONN=100
PGBOUNCER_DEFAULT_POOL_SIZE=20
PGBOUNCER_MIN_POOL_SIZE=5
```

### Docker Setup

A Docker Compose configuration is provided for running PgBouncer:

```bash
docker-compose -f docker-compose.pgbouncer.yml up -d
```

### Management Commands

The project includes a management command for checking database performance and connection pooling:

```bash
# Check database performance
python manage.py check_db_performance

# Check PgBouncer status
python manage.py check_db_performance --pgbouncer

# Show database statistics
python manage.py check_db_performance --stats

# Show slow queries
python manage.py check_db_performance --slow-queries
```

## Best Practices

1. **Use QueryMonitor for Complex Operations**: Wrap complex database operations in a QueryMonitor to track performance
2. **Optimize N+1 Queries**: Use `select_related` and `prefetch_related` to avoid N+1 query problems
3. **Monitor Slow Queries**: Regularly check the slow query log to identify performance bottlenecks
4. **Tune Connection Pool**: Adjust PgBouncer settings based on your application's needs
5. **Use Indexes**: Create appropriate indexes for frequently queried fields