from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0018_remove_flockmember_draws_remove_flockmember_losses_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Expense',
        ),
    ]
