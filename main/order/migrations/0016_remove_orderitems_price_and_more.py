# Generated by Django 4.0 on 2023-11-05 17:00

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0050_product_product_id_idx_product_product_name_namex_and_more'),
        ('order', '0015_alter_order_id'),
    ]

    operations = [
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
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
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
