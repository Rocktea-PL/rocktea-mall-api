# Generated by Django 4.0 on 2024-01-22 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0012_customuser_is_logistics'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='associated_domain',
            field=models.CharField(max_length=15, null=True, unique=True),
        ),
    ]
