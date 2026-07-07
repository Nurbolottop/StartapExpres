"""SMS-шаблоны одноразовых кодов (OTP): сброс пароля и верификация телефона.

Data-миграция, а не seed: без этих шаблонов эндпоинты
/auth/password-reset/ и /auth/verify/ не могут отправить код.
"""

from django.db import migrations

TEMPLATES = [
    # (name, language, title, body)
    (
        'auth.password_reset_code',
        'ru',
        'Восстановление пароля',
        'Код для сброса пароля: {{code}}. Действует 10 минут. Никому не сообщайте его.',
    ),
    (
        'auth.password_reset_code',
        'ky',
        'Сырсөздү калыбына келтирүү',
        'Сырсөздү калыбына келтирүү коду: {{code}}. 10 мүнөт жарактуу. Эч кимге айтпаңыз.',
    ),
    (
        'auth.password_reset_code',
        'en',
        'Password reset',
        'Your password reset code: {{code}}. Valid for 10 minutes. Do not share it.',
    ),
    (
        'auth.verify_code',
        'ru',
        'Подтверждение телефона',
        'Код подтверждения телефона: {{code}}. Действует 10 минут.',
    ),
    (
        'auth.verify_code',
        'ky',
        'Телефонду ырастоо',
        'Телефонду ырастоо коду: {{code}}. 10 мүнөт жарактуу.',
    ),
    (
        'auth.verify_code',
        'en',
        'Phone verification',
        'Your phone verification code: {{code}}. Valid for 10 minutes.',
    ),
]


def create_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    for name, language, title, body in TEMPLATES:
        NotificationTemplate.objects.get_or_create(
            name=name,
            type='sms',
            language=language,
            defaults={'title': title, 'body': body},
        )


def remove_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    NotificationTemplate.objects.filter(
        name__in=('auth.password_reset_code', 'auth.verify_code'), type='sms'
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0003_device'),
    ]

    operations = [
        migrations.RunPython(create_templates, remove_templates),
    ]
