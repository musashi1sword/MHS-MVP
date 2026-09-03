from django.contrib import admin

from .models import Appointment, ProviderSlot


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "provider", "status", "scheduled_start")
    list_filter = ("status", "mode")


admin.site.register(ProviderSlot)
