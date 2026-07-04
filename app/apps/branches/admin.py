from django.contrib import admin

from apps.branches.models import Branch, City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'phone', 'is_main', 'is_active')
    list_filter = ('city', 'is_main', 'is_active')
    search_fields = ('name', 'code', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')
