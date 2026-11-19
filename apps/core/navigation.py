"""Notification summaries for the persistent workspace top bar."""

from datetime import timedelta

from django.db.models import F
from django.utils import timezone


def get_navigation_alerts(user):
    """Return the counts and previews used by the top-bar notification bell.

    This runs only when the notification panel is actually rendered, so normal
    page loads do not pay for extra health and inventory queries.
    """
    # Imported lazily so this module stays import-safe during project start-up
    # and management commands.
    from apps.info.models import HealthRecord, Medicine

    today = timezone.localdate()
    due_cutoff = today + timedelta(days=30)
    expiry_cutoff = today + timedelta(days=30)

    health = HealthRecord.objects.filter(
        bird__user=user,
        next_due_date__isnull=False,
    )
    overdue_qs = (
        health.filter(next_due_date__lt=today)
        .select_related('bird')
        .order_by('next_due_date')
    )
    due_soon_qs = (
        health.filter(next_due_date__gte=today, next_due_date__lte=due_cutoff)
        .select_related('bird')
        .order_by('next_due_date')
    )

    inventory = Medicine.objects.filter(user=user)
    low_stock_qs = inventory.filter(
        stock_quantity__lte=F('low_stock_threshold'),
    ).order_by('stock_quantity', 'name')
    expiring_qs = inventory.filter(
        expiration_date__gte=today,
        expiration_date__lte=expiry_cutoff,
    ).order_by('expiration_date')
    expired_qs = inventory.filter(
        expiration_date__lt=today,
    ).order_by('expiration_date')

    overdue_count = overdue_qs.count()
    due_soon_count = due_soon_qs.count()
    low_stock_count = low_stock_qs.count()
    expiring_count = expiring_qs.count()
    expired_count = expired_qs.count()

    return {
        'nav_alerts': {
            'total': (
                overdue_count + due_soon_count + low_stock_count
                + expiring_count + expired_count
            ),
            'overdue_count': overdue_count,
            'due_soon_count': due_soon_count,
            'low_stock_count': low_stock_count,
            'expiring_count': expiring_count,
            'expired_count': expired_count,
            'overdue_records': list(overdue_qs[:3]),
            'due_soon_records': list(due_soon_qs[:2]),
            'low_stock_items': list(low_stock_qs[:3]),
            'expiring_items': list(expiring_qs[:2]),
            'expired_items': list(expired_qs[:2]),
        }
    }
