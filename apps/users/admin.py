from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class AgriUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Agri-Conseil", {"fields": ("role", "telephone")}),)
