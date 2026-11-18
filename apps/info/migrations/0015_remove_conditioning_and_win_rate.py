from django.db import migrations, models


def activate_conditioning_birds(apps, schema_editor):
    """Move birds out of the removed Conditioning status."""
    FlockMember = apps.get_model('info', 'FlockMember')
    FlockMember.objects.filter(status='Conditioning').update(status='Active')


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0014_delete_flocksale'),
    ]

    operations = [
        migrations.RunPython(activate_conditioning_birds, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name='conditioningsession',
            name='info_condit_bird_id_d2572a_idx',
        ),
        migrations.RemoveIndex(
            model_name='conditioningsession',
            name='info_condit_bird_id_30c43a_idx',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_feed_plan',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_notes',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_phase',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_program',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_start_date',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='conditioning_target_date',
        ),
        migrations.RemoveField(
            model_name='flockmember',
            name='target_weight_grams',
        ),
        migrations.AlterField(
            model_name='flockmember',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Broodcock', 'Broodcock'), ('Broodhen', 'Broodhen'), ('Retired', 'Retired'), ('Sold', 'Sold')], default='Active', max_length=20),
        ),
        migrations.DeleteModel(
            name='ConditioningSession',
        ),
    ]
