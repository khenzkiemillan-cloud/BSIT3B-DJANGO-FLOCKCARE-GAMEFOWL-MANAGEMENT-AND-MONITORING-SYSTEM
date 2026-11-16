# Add optional bird relation to financial entries

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0009_financialentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialentry',
            name='bird',
            field=models.ForeignKey(blank=True, help_text='Optional flock member related to this entry (e.g. bird sale, treatment cost, entry fee).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='financial_entries', to='info.flockmember'),
        ),
    ]
