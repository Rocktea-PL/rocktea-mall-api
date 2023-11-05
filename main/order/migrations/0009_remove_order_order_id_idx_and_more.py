# Generated by Django 4.0 on 2023-11-05 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0050_product_product_id_idx_product_product_name_namex_and_more'),
        ('order', '0008_alter_order_buyer'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='order',
            name='order_id_idx',
        ),
        migrations.RemoveIndex(
            model_name='order',
            name='order_buyer_buyerx',
        ),
        migrations.RemoveIndex(
            model_name='order',
            name='order_store_storex',
        ),
        migrations.RemoveField(
            model_name='order',
            name='store',
        ),
        migrations.RemoveField(
            model_name='orderitems',
            name='price',
        ),
        migrations.RemoveField(
            model_name='orderitems',
            name='total_price',
        ),
        migrations.AddField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='buyer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='mall.customuser'),
        ),
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_address',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('In-Review', 'In-Review')], default='Pending', max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='orderitems',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='order.order'),
        ),
        migrations.RemoveField(
            model_name='orderitems',
            name='product',
        ),
        migrations.AddField(
            model_name='orderitems',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_orders', to='mall.product'),
        ),
    ]
