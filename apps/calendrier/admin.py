from django.contrib import admin
from .models import Stade, CalendrierAgricole, OperationAgricole
admin.site.register([Stade, CalendrierAgricole, OperationAgricole])
