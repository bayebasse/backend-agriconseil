from rest_framework import serializers
from .models import Photo, AnalyseIA
class AnalyseSerializer(serializers.ModelSerializer):
    class Meta: model = AnalyseIA; fields = ["id","date_analyse","probleme","confiance","resultat","conseil"]
class PhotoSerializer(serializers.ModelSerializer):
    analyse = AnalyseSerializer(read_only=True)
    class Meta:
        model = Photo
        fields = ["id","culture_suivie","image","date_prise","analyse"]
        read_only_fields = ["agriculteur"]
    def create(self, validated_data):
        return Photo.objects.create(agriculteur=self.context["request"].user, **validated_data)
