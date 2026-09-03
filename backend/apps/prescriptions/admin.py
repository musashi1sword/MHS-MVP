from django.contrib import admin

from .models import DrugInteraction, Medication, Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "prescriber", "pharmacy", "status", "allergen_alert_triggered")
    list_filter = ("status", "allergen_alert_triggered")
    inlines = [PrescriptionItemInline]


admin.site.register(Medication)
admin.site.register(DrugInteraction)
