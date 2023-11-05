# Generated by Django 4.0 on 2023-11-05 16:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0050_product_product_id_idx_product_product_name_namex_and_more'),
        ('order', '0010_alter_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='mall.store'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['id'], name='order_id_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['buyer'], name='order_buyer_buyerx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['store'], name='order_store_storex'),
        ),
    ]
