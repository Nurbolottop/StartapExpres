from django.contrib import admin

from apps.branches.models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'phone', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'code', 'city')
    readonly_fields = ('id', 'created_at', 'updated_at')
