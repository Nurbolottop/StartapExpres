"""Фоновые финансовые задачи (ТЗ, раздел 11)."""

from celery import shared_task
from django.utils import timezone


@shared_task(name='finance.build_daily_report')
def build_daily_report() -> str:
    from apps.finance.services import ReportService

    report = ReportService.build('daily', timezone.localdate())
    return str(report.id)


@shared_task(name='finance.build_monthly_report')
def build_monthly_report() -> str:
    from apps.finance.services import ReportService

    report = ReportService.build('monthly', timezone.localdate().replace(day=1))
    return str(report.id)


@shared_task(name='finance.check_overdue_debts')
def check_overdue_debts_task() -> int:
    from apps.finance.services import check_overdue_debts

    return check_overdue_debts()
