const token = process.env.JWT_TOKEN || '';
const ws = new WebSocket(`ws://localhost:8000/ws/?token=${token}`);
ws.onopen = () => console.log('WebSocket connected successfully');
ws.onmessage = (event) => console.log('Received:', event.data);
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = (event) => console.log('WebSocket closed:', event.code, event.reason);
