# API Documentation

Trojan Defender provides a comprehensive REST API for all functionality. This document covers authentication, endpoints, request/response formats, and examples.

## Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [File Scanner](#file-scanner-endpoints)
  - [Threat Map](#threat-map-endpoints)
  - [Chatbot](#chatbot-endpoints)
  - [Reports](#reports-endpoints)
  - [Notifications](#notifications-endpoints)
- [WebSocket API](#websocket-api)
- [SDK Examples](#sdk-examples)

## Authentication

Trojan Defender uses JWT (JSON Web Token) authentication. All API requests (except registration and login) require a valid JWT token.

### Getting a Token

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Using the Token

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Refresh

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://your-domain.com/api`

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/endpoint/?page=3",
  "previous": "http://localhost:8000/api/endpoint/?page=1",
  "results": [
    // Array of objects
  ]
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_name": ["This field is required."]
    }
  }
}
```

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 413 | Payload Too Large |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_ERROR` | Invalid credentials |
| `PERMISSION_DENIED` | Insufficient permissions |
| `FILE_TOO_LARGE` | File exceeds size limit |
| `UNSUPPORTED_FILE_TYPE` | File type not supported |
| `SCAN_TIMEOUT` | Scan operation timed out |
| `SCAN_ERROR` | Error during file scanning |

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **File uploads**: 10 uploads/hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register/
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

#### Login
```http
POST /api/auth/login/
```

#### Logout
```http
POST /api/auth/logout/
```

#### User Profile
```http
GET /api/auth/user/
```

### File Scanner Endpoints

#### Upload and Scan File
```http
POST /api/scanner/upload/
Content-Type: multipart/form-data
```

**Request:**
```
file: [binary file data]
notify_email: user@example.com (optional)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid-here",
    "filename": "document.pdf",
    "file_size": 1024000,
    "status": "queued",
    "estimated_time": 30
  }
}
```

#### Get Scan Results
```http
GET /api/scanner/results/{scan_id}/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid-here",
    "filename": "document.pdf",
    "status": "completed",
    "threat_detected": false,
    "scan_results": {
      "clamav": {
        "clean": true,
        "signature": null
      },
      "yara": {
        "matches": []
      }
    },
    "file_info": {
      "size": 1024000,
      "mime_type": "application/pdf",
      "hash_md5": "d41d8cd98f00b204e9800998ecf8427e",
      "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:15Z"
  }
}
```

#### List Scan History
```http
GET /api/scanner/history/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status`: Filter by status (`queued`, `scanning`, `completed`, `failed`)
- `threat_detected`: Filter by threat detection (`true`, `false`)
- `date_from`: Filter from date (ISO format)
- `date_to`: Filter to date (ISO format)

#### Download Report
```http
GET /api/scanner/report/{scan_id}/
```

**Query Parameters:**
- `format`: Report format (`pdf`, `json`) (default: `pdf`)

### Threat Map Endpoints

#### Get Threat Data
```http
GET /api/threatmap/threats/
```

**Query Parameters:**
- `country`: Filter by country code
- `threat_type`: Filter by threat type
- `time_range`: Time range (`1h`, `24h`, `7d`, `30d`) (default: `24h`)

**Response:**
```json
{
  "success": true,
  "data": {
    "threats": [
      {
        "id": "threat-1",
        "country": "US",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "threat_type": "malware",
        "severity": "high",
        "timestamp": "2024-01-15T10:30:00Z",
        "description": "Trojan detected"
      }
    ],
    "statistics": {
      "total_threats": 1250,
      "by_type": {
        "malware": 800,
        "phishing": 300,
        "ransomware": 150
      },
      "by_severity": {
        "low": 500,
        "medium": 400,
        "high": 250,
        "critical": 100
      }
    }
  }
}
```

#### Get Threat Statistics
```http
GET /api/threatmap/statistics/
```

### Chatbot Endpoints

#### Send Message
```http
POST /api/chatbot/chat/
```

**Request:**
```json
{
  "message": "What is a Trojan virus?",
  "conversation_id": "uuid-here" // optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "msg-uuid",
    "message": "A Trojan virus is a type of malware that disguises itself as legitimate software...",
    "conversation_id": "conv-uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Conversations
```http
GET /api/chatbot/conversations/
```

#### Get Conversation Messages
```http
GET /api/chatbot/conversations/{conversation_id}/messages/
```

#### Get Security Topics
```http
GET /api/chatbot/topics/
```

**Response:**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "name": "Malware Detection",
      "description": "Understanding different types of malware and how to detect them",
      "icon": "shield-virus",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Security Resources
```http
GET /api/chatbot/resources/
```

### Reports Endpoints

#### Generate Report
```http
POST /api/reports/generate/
```

**Request:**
```json
{
  "report_type": "scan_summary",
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "format": "pdf",
  "filters": {
    "threat_detected": true
  }
}
```

#### List Reports
```http
GET /api/reports/
```

#### Download Report
```http
GET /api/reports/{report_id}/download/
```

### Notifications Endpoints

#### Get Notifications
```http
GET /api/notifications/
```

#### Mark as Read
```http
PATCH /api/notifications/{notification_id}/
```

**Request:**
```json
{
  "is_read": true
}
```

#### Notification Settings
```http
GET /api/notifications/settings/
PUT /api/notifications/settings/
```

## WebSocket API

Trojan Defender provides real-time updates via WebSocket connections.

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
```

### Authentication
Send JWT token after connection:
```javascript
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Message Types

#### Scan Status Update
```json
{
  "type": "scan_update",
  "data": {
    "scan_id": "uuid-here",
    "status": "completed",
    "threat_detected": false
  }
}
```

#### Threat Alert
```json
{
  "type": "threat_alert",
  "data": {
    "threat_type": "malware",
    "severity": "high",
    "location": "US",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## SDK Examples

### Python

```python
import requests

class TrojanDefenderAPI:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def login(self, email, password):
        response = self.session.post(
            f'{self.base_url}/auth/login/',
            json={'email': email, 'password': password}
        )
        data = response.json()
        self.token = data['access']
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
        return data
    
    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f'{self.base_url}/scanner/upload/',
                files={'file': f}
            )
        return response.json()
    
    def get_scan_results(self, scan_id):
        response = self.session.get(
            f'{self.base_url}/scanner/results/{scan_id}/'
        )
        return response.json()

# Usage
api = TrojanDefenderAPI('http://localhost:8000/api')
api.login('user@example.com', 'password')
result = api.upload_file('/path/to/file.exe')
print(result)
```

### JavaScript

```javascript
class TrojanDefenderAPI {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    return response.json();
  }

  async login(email, password) {
    const data = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.token = data.access;
    return data;
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request('/scanner/upload/', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it
      body: formData,
    });
  }

  async getScanResults(scanId) {
    return this.request(`/scanner/results/${scanId}/`);
  }
}

// Usage
const api = new TrojanDefenderAPI('http://localhost:8000/api');
await api.login('user@example.com', 'password');
const result = await api.uploadFile(fileInput.files[0]);
console.log(result);
```

### cURL Examples

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

#### Upload File
```bash
curl -X POST http://localhost:8000/api/scanner/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/file.exe"
```

#### Get Scan Results
```bash
curl -X GET http://localhost:8000/api/scanner/results/SCAN_ID/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Best Practices

1. **Always use HTTPS in production**
2. **Store JWT tokens securely** (httpOnly cookies recommended)
3. **Implement proper error handling**
4. **Respect rate limits**
5. **Use pagination for large datasets**
6. **Validate file types and sizes before upload**
7. **Monitor API usage and performance**

## Support

For API support:
- **Documentation**: Check this guide and inline API docs
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord for discussions
- **Email**: Contact api-support@example.com