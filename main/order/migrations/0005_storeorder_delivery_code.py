# Generated by Django 4.0 on 2024-01-18 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_alter_storeorder_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeorder',
            name='delivery_code',
            field=models.CharField(max_length=5, null=True),
        ),
    ]