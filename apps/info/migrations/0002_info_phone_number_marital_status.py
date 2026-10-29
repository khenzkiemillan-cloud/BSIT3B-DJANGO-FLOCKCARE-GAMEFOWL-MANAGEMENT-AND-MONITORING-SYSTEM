from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='info',
            name='phone_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='info',
            name='marital_status',
            field=models.CharField(
                choices=[('married', 'Married'), ('single', 'Single')],
                blank=True,
                default='',
                max_length=10,
            ),
        ),
    ]
