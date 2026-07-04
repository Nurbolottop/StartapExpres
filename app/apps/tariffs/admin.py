from django.contrib import admin

from apps.tariffs.models import AdditionalService, Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'from_city',
        'to_city',
        'base_price',
        'price_per_kg',
        'min_price',
        'is_active',
    )
    list_filter = ('is_active', 'from_city', 'to_city')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'is_active')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
