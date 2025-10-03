const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4MTAzODk0LCJpYXQiOjE3NTgxMDAyOTQsImp0aSI6ImEyZGI3ZDQxMWE1NzQ1YmU5Y2U4ZGMxOTY0ZTk4MDI1IiwidXNlcl9pZCI6IjgifQ.XX61zRU214uYPcj3BSowHxuA1h_OJGX1cZ4eO8DZ-ug';
const ws = new WebSocket('ws://localhost:8000/ws/?token=' + token);
ws.onopen = () => console.log('WebSocket connected successfully');
ws.onmessage = (event) => console.log('Received:', event.data);
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = (event) => console.log('WebSocket closed:', event.code, event.reason);
