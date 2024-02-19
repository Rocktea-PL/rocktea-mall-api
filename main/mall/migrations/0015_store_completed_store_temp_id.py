# Generated by Django 4.0 on 2024-02-12 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0014_customuser_is_operations'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='store',
            name='temp_id',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
    ]