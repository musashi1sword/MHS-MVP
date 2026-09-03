from django.contrib import admin

from .models import PatientProfile, ProviderProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "role", "clinic")
    list_filter = ("role",)
    search_fields = ("email", "first_name", "last_name")


admin.site.register(PatientProfile)
admin.site.register(ProviderProfile)
