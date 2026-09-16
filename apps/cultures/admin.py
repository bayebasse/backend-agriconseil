from django.contrib import admin
from .models import Region, Departement, CommuneLocalite, CultureRef, CultureSuivie
admin.site.register([Region, Departement, CommuneLocalite, CultureRef, CultureSuivie])
