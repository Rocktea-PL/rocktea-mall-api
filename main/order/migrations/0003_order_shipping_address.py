# Generated by Django 4.0 on 2023-10-19 13:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_order_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.CharField(max_length=400, null=True),
        ),
    ]