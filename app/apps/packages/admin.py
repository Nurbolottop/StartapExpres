from django.contrib import admin

from apps.packages.models import Package, PackagePhoto


class PackagePhotoInline(admin.TabularInline):
    model = PackagePhoto
    extra = 0
    readonly_fields = ('image', 'type', 'uploaded_by', 'created_at')
    can_delete = False


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'status', 'weight', 'volume', 'qr_code', 'fragile', 'dangerous')
    list_filter = ('status', 'fragile', 'dangerous')
    search_fields = ('title', 'qr_code', 'barcode', 'order__order_number')
    readonly_fields = ('id', 'qr_code', 'barcode', 'qr_generated_at', 'status', 'created_at', 'updated_at')
    inlines = (PackagePhotoInline,)
