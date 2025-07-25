# Generated by Django 5.1.2 on 2025-01-13 16:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0019_storeorder_tracking_id_storeorder_tracking_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paystackwebhook',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.storeorder'),
        ),
        migrations.AddField(
            model_name='storeorder',
            name='shipping_fee',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=11, null=True),
        ),
    ]
