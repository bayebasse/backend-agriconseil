from django.contrib import admin
from .models import DonneeMeteo, ConsultationMeteo
admin.site.register([DonneeMeteo, ConsultationMeteo])
