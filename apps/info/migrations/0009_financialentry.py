# Generated manually for expenses/financial tracker

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0008_flockmember_conditioning_feed_plan_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_type', models.CharField(choices=[('expense', 'Expense'), ('income', 'Income')], default='expense', max_length=10)),
                ('category', models.CharField(choices=[('Feed', 'Feed & Supplements'), ('Medicine', 'Medicine & Health'), ('Equipment', 'Equipment & Supplies'), ('Transport', 'Transport'), ('Entry Fee', 'Entry Fee'), ('Labor', 'Labor'), ('Utilities', 'Utilities'), ('Other', 'Other Expense'), ('Bird Sale', 'Bird Sale'), ('Prize Money', 'Prize Money'), ('Stud Fee', 'Stud Fee'), ('Other', 'Other Income')], default='Feed', max_length=30)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date', models.DateField()),
                ('description', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='financialentry',
            index=models.Index(fields=['user', 'date'], name='info_financ_user_id_d7f3a1_idx'),
        ),
        migrations.AddIndex(
            model_name='financialentry',
            index=models.Index(fields=['user', 'entry_type'], name='info_financ_user_id_e2b4c9_idx'),
        ),
    ]
