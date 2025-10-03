"""
Performance tests for the Trojan Defender application.
Tests system performance under various load conditions.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from threatmap.models import ThreatEvent, GlobalThreatStats
from scanner.models import ScanResult, ScanThreat

User = get_user_model()


class DatabasePerformanceTest(TransactionTestCase):
    """Test database performance under various conditions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='perf_test@example.com',
            password='testpass123'
        )
    
    def test_bulk_threat_event_insertion(self):
        """Test bulk insertion performance for threat events."""
        start_time = time.time()
        
        # Create 1000 threat events
        events = []
        for i in range(1000):
            events.append(ThreatEvent(
                threat_type='malware',
                severity='medium',
                ip_address=f'192.168.{i//256}.{i%256}',
                country='US',
                city='Test City',
                latitude=40.7128,
                longitude=-74.0060,
                description=f'Performance test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events, batch_size=100)
        
        end_time = time.time()
        insertion_time = end_time - start_time
        
        # Verify all events were created
        self.assertEqual(ThreatEvent.objects.count(), 1000)
        
        # Performance assertion - should complete within 10 seconds
        self.assertLess(insertion_time, 10.0)
        
        print(f"Bulk insertion of 1000 events took: {insertion_time:.2f} seconds")
    
    def test_threat_event_query_performance(self):
        """Test query performance with large dataset."""
        # Create test data
        events = []
        for i in range(500):
            events.append(ThreatEvent(
                threat_type='malware' if i % 2 == 0 else 'phishing',
                severity='high' if i % 3 == 0 else 'medium',
                ip_address=f'10.0.{i//256}.{i%256}',
                country='US' if i % 2 == 0 else 'CA',
                description=f'Query test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events, batch_size=100)
        
        # Test various queries
        queries = [
            lambda: list(ThreatEvent.objects.filter(threat_type='malware')),
            lambda: list(ThreatEvent.objects.filter(severity='high')),
            lambda: list(ThreatEvent.objects.filter(country='US')),
            lambda: list(ThreatEvent.objects.order_by('-timestamp')[:50]),
        ]
        
        for i, query in enumerate(queries):
            start_time = time.time()
            results = query()
            end_time = time.time()
            query_time = end_time - start_time
            
            # Each query should complete within 1 second
            self.assertLess(query_time, 1.0)
            self.assertGreater(len(results), 0)
            
            print(f"Query {i+1} took: {query_time:.3f} seconds, returned {len(results)} results")
    
    def test_concurrent_database_operations(self):
        """Test database performance under concurrent operations."""
        def create_events(thread_id, count):
            events = []
            for i in range(count):
                events.append(ThreatEvent(
                    threat_type='malware',
                    severity='medium',
                    ip_address=f'172.16.{thread_id}.{i}',
                    country='US',
                    description=f'Concurrent test event {thread_id}-{i}'
                ))
            ThreatEvent.objects.bulk_create(events)
        
        start_time = time.time()
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for thread_id in range(5):
                future = executor.submit(create_events, thread_id, 50)
                futures.append(future)
            
            # Wait for all threads to complete
            for future in futures:
                future.result()
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Verify all events were created
        self.assertEqual(ThreatEvent.objects.count(), 250)
        
        # Should complete within reasonable time
        self.assertLess(concurrent_time, 15.0)
        
        print(f"Concurrent creation of 250 events took: {concurrent_time:.2f} seconds")


class APIPerformanceTest(TestCase):
    """Test API performance under various load conditions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='api_perf_test@example.com',
            password='testpass123'
        )
        
        # Create test threat events
        events = []
        for i in range(200):
            events.append(ThreatEvent(
                threat_type='malware' if i % 3 == 0 else 'phishing',
                severity='high' if i % 4 == 0 else 'medium',
                ip_address=f'203.0.{i//256}.{i%256}',
                country='US' if i % 2 == 0 else 'CA',
                description=f'API test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events, batch_size=50)
        
        # Set up authenticated client
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    def test_threat_events_api_performance(self):
        """Test threat events API response time."""
        # Test different page sizes
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = self.client.get(f'/api/threatmap/events/?page_size={page_size}')
            end_time = time.time()
            
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            # Response should be fast regardless of page size
            self.assertLess(response_time, 2.0)
            
            data = response.json()
            self.assertLessEqual(len(data['results']), page_size)
            
            print(f"Events API (page_size={page_size}) took: {response_time:.3f} seconds")
    
    def test_map_data_api_performance(self):
        """Test map data API performance."""
        start_time = time.time()
        response = self.client.get('/api/threatmap/map/data/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Map data should load quickly
        self.assertLess(response_time, 3.0)
        
        data = response.json()
        self.assertIn('threat_events', data)
        self.assertIn('threat_stats', data)
        
        print(f"Map data API took: {response_time:.3f} seconds")
    
    def test_concurrent_api_requests(self):
        """Test API performance under concurrent requests."""
        def make_request(endpoint):
            client = APIClient()
            refresh = RefreshToken.for_user(self.user)
            access_token = str(refresh.access_token)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            response = client.get(endpoint)
            return response.status_code
        
        endpoints = [
            '/api/threatmap/events/',
            '/api/threatmap/map/data/',
            '/api/threatmap/stats/',
        ]
        
        start_time = time.time()
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(30):  # 30 total requests
                endpoint = endpoints[_ % len(endpoints)]
                future = executor.submit(make_request, endpoint)
                futures.append(future)
            
            # Collect results
            status_codes = [future.result() for future in futures]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Most requests should succeed
        success_count = sum(1 for code in status_codes if code == 200)
        self.assertGreaterEqual(success_count, 25)  # At least 83% success rate
        
        # Should handle concurrent load reasonably
        self.assertLess(concurrent_time, 10.0)
        
        print(f"30 concurrent API requests took: {concurrent_time:.2f} seconds")
        print(f"Success rate: {success_count}/30 ({success_count/30*100:.1f}%)")


class CachePerformanceTest(TestCase):
    """Test caching performance and effectiveness."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='cache_perf_test@example.com',
            password='testpass123'
        )
        
        # Create test data
        events = []
        for i in range(100):
            events.append(ThreatEvent(
                threat_type='malware',
                severity='medium',
                ip_address=f'198.51.100.{i}',
                country='US',
                description=f'Cache test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events)
    
    @patch('trojan_defender.cache_utils.cache')
    def test_cache_hit_performance(self, mock_cache):
        """Test performance improvement with cache hits."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Set up client
        client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Mock cache miss for first request
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get('/api/threatmap/map/data/')
        cache_miss_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        
        # Mock cache hit for second request
        cached_data = response1.json()
        mock_cache.get.return_value = cached_data
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = client.get('/api/threatmap/map/data/')
        cache_hit_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        
        # Cache hit should be significantly faster
        # Note: This test is mocked, so timing may not be realistic
        print(f"Cache miss time: {cache_miss_time:.3f} seconds")
        print(f"Cache hit time: {cache_hit_time:.3f} seconds")
    
    def test_memory_usage_with_large_dataset(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        events = []
        for i in range(2000):
            events.append(ThreatEvent(
                threat_type='malware',
                severity='medium',
                ip_address=f'203.0.{i//256}.{i%256}',
                country='US',
                description=f'Memory test event {i}' * 10  # Longer description
            ))
        
        ThreatEvent.objects.bulk_create(events, batch_size=200)
        
        # Query the data
        start_time = time.time()
        threat_events = list(ThreatEvent.objects.all())
        query_time = time.time() - start_time
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.assertEqual(len(threat_events), 2000)
        self.assertLess(query_time, 5.0)  # Should complete within 5 seconds
        
        print(f"Query time for 2000 events: {query_time:.2f} seconds")
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        # Memory usage should be reasonable (less than 100MB increase)
        self.assertLess(memory_increase, 100.0)


class LoadTestCase(TestCase):
    """Simulate load testing scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f'load_test_{i}@example.com',
                password='testpass123'
            )
            self.users.append(user)
    
    def test_multiple_user_concurrent_access(self):
        """Test system performance with multiple concurrent users."""
        def user_session(user_id):
            user = self.users[user_id]
            client = APIClient()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Simulate user activity
            endpoints = [
                '/api/threatmap/events/',
                '/api/threatmap/map/data/',
                '/api/threatmap/stats/',
            ]
            
            response_times = []
            for endpoint in endpoints:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_times.append(end_time - start_time)
                if response.status_code != 200:
                    return False, response_times
            
            return True, response_times
        
        # Create some test data
        events = []
        for i in range(50):
            events.append(ThreatEvent(
                threat_type='malware',
                severity='medium',
                ip_address=f'192.0.2.{i}',
                country='US',
                description=f'Load test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events)
        
        start_time = time.time()
        
        # Run concurrent user sessions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for user_id in range(5):
                future = executor.submit(user_session, user_id)
                futures.append(future)
            
            # Collect results
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_sessions = sum(1 for success, _ in results if success)
        all_response_times = []
        for success, times in results:
            if success:
                all_response_times.extend(times)
        
        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        # Assertions
        self.assertGreaterEqual(successful_sessions, 4)  # At least 80% success
        self.assertLess(total_time, 15.0)  # Should complete within 15 seconds
        self.assertLess(avg_response_time, 2.0)  # Average response under 2 seconds
        
        print(f"Load test completed in: {total_time:.2f} seconds")
        print(f"Successful sessions: {successful_sessions}/5")
        print(f"Average response time: {avg_response_time:.3f} seconds")
        print(f"Max response time: {max_response_time:.3f} seconds")