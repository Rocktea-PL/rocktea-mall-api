# Generated by Django 4.0 on 2023-10-24 16:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0022_marketplace_profit_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='marketplace',
            name='price',
        ),
        migrations.RemoveField(
            model_name='marketplace',
            name='profit_price',
        ),
    ]
