from django.contrib import admin

from .models import (
    BreedingRecord,
    Chicken,
    ChickenClassification,
    Expense,
    FeedRecord,
    HealthRecord,
    Supply,
)


@admin.register(Chicken)
class ChickenAdmin(admin.ModelAdmin):
    list_display = ('chicken_code', 'name', 'breed', 'gender', 'status', 'classification')
    list_filter = ('status', 'gender', 'classification')
    search_fields = ('chicken_code', 'name', 'breed')


@admin.register(ChickenClassification)
class ChickenClassificationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(BreedingRecord)
class BreedingRecordAdmin(admin.ModelAdmin):
    list_display = ('male_chicken', 'female_chicken', 'breeding_date')
    list_filter = ('breeding_date',)
    search_fields = ('male_chicken__chicken_code', 'female_chicken__chicken_code')


@admin.register(HealthRecord)
class CoreHealthRecordAdmin(admin.ModelAdmin):
    list_display = ('chicken', 'health_condition', 'checkup_date')
    list_filter = ('checkup_date',)
    search_fields = ('chicken__chicken_code', 'health_condition', 'vaccination')


@admin.register(FeedRecord)
class FeedRecordAdmin(admin.ModelAdmin):
    list_display = ('chicken', 'feed_type', 'quantity', 'feeding_date')
    list_filter = ('feeding_date', 'feed_type')
    search_fields = ('chicken__chicken_code', 'feed_type')


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'supply_type', 'quantity', 'unit', 'minimum_stock', 'expiration_date')
    list_filter = ('supply_type',)
    search_fields = ('name', 'unit')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_name', 'amount', 'expense_date')
    list_filter = ('expense_date',)
    search_fields = ('expense_name', 'description')
