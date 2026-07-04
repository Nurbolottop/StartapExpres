from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message='Номер телефона в международном формате, например +996700123456 (9–15 цифр).',
)
