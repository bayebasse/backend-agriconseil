from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "telephone", "role"]
        read_only_fields = ["id", "role"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "telephone", "password"]

    def create(self, validated_data):
        return User.objects.create_user(role="farmer", **validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Identifiants invalides.")
        attrs["user"] = user
        return attrs
