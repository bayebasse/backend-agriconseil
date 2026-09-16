from django.contrib.auth import login, logout
from django.http import JsonResponse
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer

def health(request):
    return JsonResponse({"status": "ok", "service": "Agri-Conseil API"})

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = __import__("apps.users.models", fromlist=["User"]).User.objects.get(username=response.data["username"])
        token, _ = Token.objects.get_or_create(user=user)
        response.data["token"] = token.key
        return response

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({**UserSerializer(user).data, "token": token.key})

class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"detail": "Déconnexion réussie."})

class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
