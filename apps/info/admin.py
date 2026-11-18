from django.contrib import admin
from .models import (
    Breed, FlockMember, HealthRecord, Medicine, WeightLog,
    BreedingPen, ClutchRecord,
)


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FlockMember)
class FlockMemberAdmin(admin.ModelAdmin):
    list_display = ('tag_number', 'breed', 'gender', 'status', 'cage_number', 'weight_grams', 'user')
    list_filter = ('status', 'gender', 'breed', 'comb_type', 'leg_color')
    search_fields = ('tag_number', 'sire', 'dam', 'color', 'cage_number')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'category', 'stock_quantity', 'unit', 'unit_cost', 'low_stock_threshold', 'expiration_date', 'user')
    list_filter = ('item_type', 'category', 'unit')
    search_fields = ('name', 'notes')


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('bird', 'record_type', 'title', 'medicine', 'quantity_used', 'date_administered', 'next_due_date')
    list_filter = ('record_type', 'date_administered')
    search_fields = ('bird__tag_number', 'title', 'medicine__name', 'notes')


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('bird', 'date', 'time_of_day', 'weight_grams')
    list_filter = ('time_of_day', 'date')
    search_fields = ('bird__tag_number',)


@admin.register(BreedingPen)
class BreedingPenAdmin(admin.ModelAdmin):
    list_display = ('pen_number', 'sire', 'dam', 'date_paired', 'status', 'user')
    list_filter = ('status', 'date_paired')
    search_fields = ('pen_number', 'sire__tag_number', 'dam__tag_number')


@admin.register(ClutchRecord)
class ClutchRecordAdmin(admin.ModelAdmin):
    list_display = ('pen', 'clutch_number', 'date_started', 'eggs_collected', 'fertile_eggs', 'hatched_count', 'hatch_date')
    list_filter = ('date_started', 'hatch_date')
