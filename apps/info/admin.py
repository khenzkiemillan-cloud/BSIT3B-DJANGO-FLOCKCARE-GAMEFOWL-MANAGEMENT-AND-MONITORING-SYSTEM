from django.contrib import admin
from .models import Breed, FlockMember, HealthRecord, Medicine, FightRecord, WeightLog, BreedingPen, ClutchRecord


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FlockMember)
class FlockMemberAdmin(admin.ModelAdmin):
    list_display = ('tag_number', 'breed', 'gender', 'status', 'cage_number', 'wins', 'losses', 'draws', 'user')
    list_filter = ('status', 'gender', 'breed', 'comb_type', 'leg_color')
    search_fields = ('tag_number', 'sire', 'dam', 'color', 'cage_number')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'stock_quantity', 'unit', 'low_stock_threshold', 'expiration_date', 'user')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'notes')


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('bird', 'record_type', 'title', 'date_administered', 'next_due_date')
    list_filter = ('record_type', 'date_administered')
    search_fields = ('bird__tag_number', 'title', 'notes')


@admin.register(FightRecord)
class FightRecordAdmin(admin.ModelAdmin):
    list_display = ('bird', 'event_name', 'result', 'fight_date', 'weight_grams', 'opponent')
    list_filter = ('result', 'fight_date')
    search_fields = ('bird__tag_number', 'event_name', 'opponent')


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
