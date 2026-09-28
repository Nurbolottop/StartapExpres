"""Шаблоны уведомления «груз проехал город» (отметка точки маршрута водителем).

In-app и push на трёх языках: без шаблона NotificationService канал пропускает.
"""

from django.db import migrations

EVENT = 'shipment.checkpoint_reached'

TEMPLATES = [
    # (language, title, body)
    ('ru', 'Груз в пути', 'Ваш груз {{order}} проехал {{city}}'),
    ('ky', 'Жүк жолдо', '{{order}} жүгүңүз {{city}} аркылуу өттү'),
    ('en', 'Cargo on the way', 'Your cargo {{order}} has passed {{city}}'),
]
CHANNELS = ('in_app', 'push')


def create_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    for channel in CHANNELS:
        for language, title, body in TEMPLATES:
            NotificationTemplate.objects.get_or_create(
                name=EVENT,
                type=channel,
                language=language,
                defaults={'title': title, 'body': body},
            )


def remove_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    NotificationTemplate.objects.filter(name=EVENT, type__in=CHANNELS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0004_otp_sms_templates'),
    ]

    operations = [
        migrations.RunPython(create_templates, remove_templates),
    ]
