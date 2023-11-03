# Generated by Django 4.0 on 2023-11-03 07:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0050_product_product_id_idx_product_product_name_namex_and_more'),
        ('order', '0007_order_order_id_idx_order_order_buyer_buyerx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='mall.customuser'),
        ),
    ]
