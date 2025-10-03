from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class APIRoot(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "auth": {
                "token": request.build_absolute_uri("auth/token/"),
                "refresh": request.build_absolute_uri("auth/token/refresh/")
            },
            "scanner": request.build_absolute_uri("scanner/"),
            "threatmap": request.build_absolute_uri("threatmap/"),
            "notifications": request.build_absolute_uri("notifications/"),
            "threat_intelligence": request.build_absolute_uri("threat-intelligence/")
        })