# Replace the finance tracker with per-flock-member expenses.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


EXPENSE_CATEGORIES = {
    'Feed', 'Medicine', 'Equipment', 'Transport',
    'Entry Fee', 'Labor', 'Utilities', 'Other',
}


def copy_expense_entries(apps, schema_editor):
    """Move existing expense rows into the new Expense model."""
    FinancialEntry = apps.get_model('info', 'FinancialEntry')
    Expense = apps.get_model('info', 'Expense')

    for entry in FinancialEntry.objects.filter(entry_type='expense').iterator():
        expense = Expense.objects.create(
            user_id=entry.user_id,
            bird_id=entry.bird_id,
            category=entry.category if entry.category in EXPENSE_CATEGORIES else 'Other',
            amount=entry.amount,
            date=entry.date,
            description=entry.description,
            notes=entry.notes,
        )
        # Preserve the original timestamp even though created_at is auto_now_add.
        Expense.objects.filter(pk=expense.pk).update(created_at=entry.created_at)


def restore_financial_entries(apps, schema_editor):
    """Restore expenses to the old finance table when rolling back."""
    FinancialEntry = apps.get_model('info', 'FinancialEntry')
    Expense = apps.get_model('info', 'Expense')

    for expense in Expense.objects.iterator():
        entry = FinancialEntry.objects.create(
            user_id=expense.user_id,
            bird_id=expense.bird_id,
            entry_type='expense',
            category=expense.category,
            amount=expense.amount,
            date=expense.date,
            description=expense.description,
            notes=expense.notes,
        )
        FinancialEntry.objects.filter(pk=entry.pk).update(created_at=expense.created_at)


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0012_alter_flockmember_status_flocksale'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Feed', 'Feed & Supplements'), ('Medicine', 'Medicine & Health'), ('Equipment', 'Equipment & Supplies'), ('Transport', 'Transport'), ('Entry Fee', 'Entry Fee'), ('Labor', 'Labor'), ('Utilities', 'Utilities'), ('Other', 'Other Expense')], default='Feed', max_length=30)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date', models.DateField()),
                ('description', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bird', models.ForeignKey(blank=True, help_text='Flock member this expense belongs to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='info.flockmember')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-created_at'],
                'indexes': [
                    models.Index(fields=['user', 'date'], name='info_expense_user_date_idx'),
                    models.Index(fields=['user', 'bird'], name='info_expense_user_bird_idx'),
                ],
            },
        ),
        migrations.RunPython(copy_expense_entries, restore_financial_entries),
        migrations.RemoveField(
            model_name='flocksale',
            name='financial_entry',
        ),
        migrations.DeleteModel(
            name='FinancialEntry',
        ),
    ]
