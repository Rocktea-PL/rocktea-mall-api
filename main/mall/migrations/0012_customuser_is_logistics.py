# Generated by Django 4.0 on 2024-01-20 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0011_alter_reportuser_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_logistics',
            field=models.BooleanField(default=False),
        ),
    ]
