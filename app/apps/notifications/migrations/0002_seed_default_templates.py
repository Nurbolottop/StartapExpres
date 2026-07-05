"""Базовые in-app шаблоны 10 событий жизненного цикла заказа (ТЗ, разделы 04, 12)."""
from django.db import migrations

TEMPLATES = [
    ('order.created', 'Заказ создан', 'Заказ {{order}} создан. Стоимость: {{price}} сом.'),
    ('order.confirmed', 'Заказ подтверждён', 'Заказ {{order}} подтверждён оператором.'),
    ('order.paid', 'Оплата получена', 'Оплата по заказу {{order}} получена. Спасибо!'),
    ('order.received', 'Груз принят', 'Груз по заказу {{order}} принят на склад.'),
    ('order.loaded', 'Груз погружен', 'Груз по заказу {{order}} погружен в автомобиль.'),
    ('order.in_transit', 'Груз в пути', 'Заказ {{order}} отправлен и находится в пути.'),
    ('order.arrived', 'Груз прибыл', 'Заказ {{order}} прибыл в филиал назначения.'),
    ('order.ready_for_pickup', 'Готов к выдаче', 'Заказ {{order}} готов к выдаче.'),
    ('order.delivered', 'Заказ выдан', 'Заказ {{order}} выдан получателю.'),
    ('order.completed', 'Заказ завершён', 'Заказ {{order}} завершён. Ждём вас снова!'),
]


def seed(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    for name, title, body in TEMPLATES:
        NotificationTemplate.objects.get_or_create(
            name=name, type='in_app', language='ru',
            defaults={'title': title, 'body': body},
        )


def unseed(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    NotificationTemplate.objects.filter(
        name__in=[name for name, _, _ in TEMPLATES], type='in_app', language='ru'
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_create_notifications'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
