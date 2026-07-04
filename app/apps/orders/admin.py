from django.contrib import admin

from apps.orders.models import Order, OrderServiceItem, OrderStatusHistory


class OrderServiceItemInline(admin.TabularInline):
    model = OrderServiceItem
    extra = 0
    readonly_fields = ('service', 'price')
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'comment', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'client',
        'status',
        'from_branch',
        'to_branch',
        'total_price',
        'paid_amount',
        'created_at',
    )
    list_filter = ('status', 'payment_type', 'delivery_type', 'from_branch', 'to_branch')
    search_fields = ('order_number', 'sender_phone', 'receiver_phone', 'client__phone')
    readonly_fields = (
        'id',
        'order_number',
        'status',
        'version',
        'paid_amount',
        'price_details',
        'created_at',
        'updated_at',
    )
    inlines = (OrderServiceItemInline, OrderStatusHistoryInline)
