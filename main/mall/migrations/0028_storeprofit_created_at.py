# Generated by Django 4.0 on 2023-10-24 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0027_storeprofit_remove_price_profit_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeprofit',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
