# Generated by Django 4.0 on 2024-02-16 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0015_store_completed_store_temp_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='store',
            old_name='associated_domain',
            new_name='domain_name',
        ),
    ]
