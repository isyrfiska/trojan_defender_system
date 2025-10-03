import time
import logging
import functools
from django.db import connection, connections, reset_queries
from django.conf import settings
from django.db.models import QuerySet
from django.core.cache import cache

logger = logging.getLogger('api')

class QueryOptimizer:
    """
    Utility class for optimizing database queries.
    """
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None):
        """
        Optimize a queryset by adding select_related and prefetch_related.
        
        Args:
            queryset: The queryset to optimize
            select_related: List of fields to select_related
            prefetch_related: List of fields to prefetch_related
            
        Returns:
            Optimized queryset
        """
        if not isinstance(queryset, QuerySet):
            return queryset
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset
    
    @staticmethod
    def only_needed_fields(queryset, fields):
        """
        Optimize a queryset by selecting only needed fields.
        
        Args:
            queryset: The queryset to optimize
            fields: List of fields to select
            
        Returns:
            Optimized queryset
        """
        if not isinstance(queryset, QuerySet) or not fields:
            return queryset
        
        return queryset.only(*fields)
    
    @staticmethod
    def defer_large_fields(queryset, fields):
        """
        Optimize a queryset by deferring large fields.
        
        Args:
            queryset: The queryset to optimize
            fields: List of fields to defer
            
        Returns:
            Optimized queryset
        """
        if not isinstance(queryset, QuerySet) or not fields:
            return queryset
        
        return queryset.defer(*fields)
    
    @staticmethod
    def use_iterator_for_large_querysets(queryset, chunk_size=2000):
        """
        Use iterator for large querysets to reduce memory usage.
        
        Args:
            queryset: The queryset to optimize
            chunk_size: Chunk size for iterator
            
        Returns:
            Iterator for the queryset
        """
        if not isinstance(queryset, QuerySet):
            return queryset
        
        return queryset.iterator(chunk_size=chunk_size)
    
    @staticmethod
    def use_values_or_values_list(queryset, fields, flat=False):
        """
        Use values() or values_list() for better performance when only specific fields are needed.
        
        Args:
            queryset: The queryset to optimize
            fields: List of fields to select
            flat: Whether to use flat=True with values_list (only for single field)
            
        Returns:
            Optimized queryset
        """
        if not isinstance(queryset, QuerySet) or not fields:
            return queryset
        
        if len(fields) == 1 and flat:
            return queryset.values_list(fields[0], flat=True)
        
        return queryset.values(*fields)
    
    @staticmethod
    def use_bulk_create(model, objects, batch_size=100):
        """
        Use bulk_create for better performance when creating multiple objects.
        
        Args:
            model: The model class
            objects: List of model instances to create
            batch_size: Batch size for bulk_create
            
        Returns:
            Created objects
        """
        if not objects:
            return []
        
        return model.objects.bulk_create(objects, batch_size=batch_size)
    
    @staticmethod
    def use_bulk_update(objects, fields, batch_size=100):
        """
        Use bulk_update for better performance when updating multiple objects.
        
        Args:
            objects: List of model instances to update
            fields: List of fields to update
            batch_size: Batch size for bulk_update
            
        Returns:
            None
        """
        if not objects or not fields:
            return
        
        model = objects[0].__class__
        model.objects.bulk_update(objects, fields, batch_size=batch_size)
    
    @staticmethod
    def use_in_bulk(model, ids, field_name='pk'):
        """
        Use in_bulk for better performance when retrieving multiple objects by ID.
        
        Args:
            model: The model class
            ids: List of IDs
            field_name: Field name to use for lookup
            
        Returns:
            Dict of objects keyed by ID
        """
        if not ids:
            return {}
        
        return model.objects.in_bulk(ids, field_name=field_name)


def query_debugger(func):
    """
    Decorator to debug database queries.
    
    Usage:
        @query_debugger
        def my_view(request):
            # View code here
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        queries = len(connection.queries)
        execution_time = end - start
        
        logger.debug(f"Function: {func.__name__}")
        logger.debug(f"Number of queries: {queries}")
        logger.debug(f"Execution time: {execution_time:.3f}s")
        
        if queries > 10:
            logger.warning(f"High number of queries ({queries}) in {func.__name__}")
            
            # Log the actual queries for debugging
            for i, query in enumerate(connection.queries):
                logger.debug(f"Query {i+1}: {query['sql']}")
                logger.debug(f"Time: {query['time']}")
        
        return result
    
    return wrapper


class DatabaseMonitor:
    """
    Utility class for monitoring database performance.
    """
    
    @staticmethod
    def get_connection_stats():
        """
        Get statistics about database connections.
        
        Returns:
            Dict with connection statistics
        """
        stats = {}
        
        for alias in connections:
            conn = connections[alias]
            stats[alias] = {
                'vendor': conn.vendor,
                'is_usable': conn.is_usable(),
                'allow_thread_sharing': conn.allow_thread_sharing,
                'autocommit': conn.autocommit,
                'in_atomic_block': conn.in_atomic_block,
            }
        
        return stats
    
    @staticmethod
    def get_query_count():
        """
        Get the number of queries executed.
        
        Returns:
            Number of queries
        """
        return len(connection.queries) if settings.DEBUG else 0
    
    @staticmethod
    def get_slow_queries(threshold=1.0):
        """
        Get slow queries (queries that took longer than threshold seconds).
        
        Args:
            threshold: Threshold in seconds
            
        Returns:
            List of slow queries
        """
        if not settings.DEBUG:
            return []
        
        slow_queries = []
        for query in connection.queries:
            if float(query.get('time', 0)) > threshold:
                slow_queries.append(query)
        
        return slow_queries
    
    @staticmethod
    def log_database_stats():
        """
        Log database statistics.
        """
        if not settings.DEBUG:
            return
        
        stats = DatabaseMonitor.get_connection_stats()
        query_count = DatabaseMonitor.get_query_count()
        slow_queries = DatabaseMonitor.get_slow_queries()
        
        logger.info(f"Database connections: {len(stats)}")
        logger.info(f"Query count: {query_count}")
        logger.info(f"Slow queries: {len(slow_queries)}")
        
        for alias, conn_stats in stats.items():
            logger.info(f"Connection {alias}: {conn_stats}")
        
        for i, query in enumerate(slow_queries):
            logger.warning(f"Slow query {i+1}: {query['sql']}")
            logger.warning(f"Time: {query['time']}")


def cached_query(timeout=3600, key_prefix='query_cache'):
    """
    Decorator to cache database queries.
    
    Usage:
        @cached_query(timeout=3600, key_prefix='my_view')
        def my_view(request):
            # View code here
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add args and kwargs to key
            for arg in args:
                if hasattr(arg, 'pk'):
                    key_parts.append(f"arg_{arg.pk}")
                else:
                    key_parts.append(f"arg_{str(arg)}")
            
            for k, v in kwargs.items():
                if hasattr(v, 'pk'):
                    key_parts.append(f"{k}_{v.pk}")
                else:
                    key_parts.append(f"{k}_{str(v)}")
            
            cache_key = '_'.join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator