# Generated by Django 4.0 on 2023-10-24 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0024_price_profit_price_price_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='price',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
