from rest_framework import viewsets, permissions
from .models import Region, Departement, CommuneLocalite, CultureRef, CultureSuivie
from .serializers import RegionSerializer, DepartementSerializer, CommuneSerializer, CultureRefSerializer, CultureSuivieSerializer

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all().order_by("nom"); serializer_class = RegionSerializer
class DepartementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DepartementSerializer
    def get_queryset(self): return Departement.objects.filter(region_id=self.request.query_params.get("region")) if self.request.query_params.get("region") else Departement.objects.all()
class CommuneViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommuneSerializer
    def get_queryset(self): return CommuneLocalite.objects.filter(departement_id=self.request.query_params.get("departement")) if self.request.query_params.get("departement") else CommuneLocalite.objects.all()
class CultureRefViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CultureRef.objects.filter(actif=True).order_by("nom"); serializer_class = CultureRefSerializer
class CultureSuivieViewSet(viewsets.ModelViewSet):
    serializer_class = CultureSuivieSerializer
    def get_queryset(self): return CultureSuivie.objects.filter(agriculteur=self.request.user).select_related("culture","commune","region","departement").order_by("-created_at")
