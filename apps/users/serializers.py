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
    role = serializers.ChoiceField(
        choices=[("farmer", "Agriculteur"), ("buyer", "Acheteur")],
        default="farmer",
        required=False,
    )
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "telephone", "password", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", "farmer")
        return User.objects.create_user(role=role, **validated_data)

class LoginSerializer(serializers.Serializer):
    # Keep `username` for existing clients; an email may also be entered there.
    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = (attrs.get("username") or attrs.get("email") or "").strip()
        if not identifier:
            raise serializers.ValidationError({"username": "Saisissez votre nom d'utilisateur ou votre email."})

        username = identifier
        user_model = User
        if not user_model.objects.filter(username=username).exists():
            matches = user_model.objects.filter(email__iexact=identifier)
            if matches.count() == 1:
                username = matches.get().username
            elif matches.count() > 1:
                raise serializers.ValidationError("Plusieurs comptes utilisent cet email. Connectez-vous avec votre nom d'utilisateur.")

        user = authenticate(username=username, password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Identifiants invalides. Vérifiez votre nom d'utilisateur ou votre email et votre mot de passe.")
        attrs["user"] = user
        return attrs
