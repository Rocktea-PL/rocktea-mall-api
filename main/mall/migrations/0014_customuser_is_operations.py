# Generated by Django 4.0 on 2024-01-24 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0013_alter_store_associated_domain'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_operations',
            field=models.BooleanField(default=False),
        ),
    ]
