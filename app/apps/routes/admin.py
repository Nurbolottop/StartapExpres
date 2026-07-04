from django.contrib import admin

from apps.routes.models import Route, RoutePoint


class RoutePointInline(admin.TabularInline):
    model = RoutePoint
    extra = 0


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'start_branch',
        'end_branch',
        'estimated_distance',
        'estimated_duration',
        'is_active',
    )
    search_fields = ('name', 'code')
    list_filter = ('is_active',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (RoutePointInline,)
