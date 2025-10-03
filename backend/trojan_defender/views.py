from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

def serve_react_app(request):
    """
    Serve the React frontend for all non-API routes
    This handles React Router client-side routing
    """
    try:
        # In production, serve the built React app
        index_file_path = os.path.join(settings.BASE_DIR, '..', 'frontend', 'dist', 'index.html')
        if os.path.exists(index_file_path):
            with open(index_file_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
    except Exception:
        pass
    
    # Development fallback - redirect to Vite dev server
    return HttpResponse(
        '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trojan Defender</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div id="root">
                <h1>Trojan Defender</h1>
                <p>Development Mode:</p>
                <ul>
                    <li><strong>Frontend:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></li>
                    <li><strong>Backend API:</strong> <a href="http://localhost:8000/api/" target="_blank">http://localhost:8000/api/</a></li>
                    <li><strong>Admin:</strong> <a href="http://localhost:8000/admin/" target="_blank">http://localhost:8000/admin/</a></li>
                    <li><strong>API Docs:</strong> <a href="http://localhost:8000/swagger/" target="_blank">http://localhost:8000/swagger/</a></li>
                </ul>
                <p>Please start the frontend with: <code>cd frontend && npm run dev</code></p>
            </div>
        </body>
        </html>
        ''',
        content_type='text/html'
    )