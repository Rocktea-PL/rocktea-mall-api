# Generated by Django 4.0 on 2023-10-25 11:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0031_price_base_price_price_store_alter_price_product'),
    ]

    operations = [
        migrations.RenameField(
            model_name='price',
            old_name='base_price',
            new_name='profit_price',
        ),
    ]
