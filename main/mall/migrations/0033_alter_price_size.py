# Generated by Django 4.0 on 2023-10-25 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0032_rename_base_price_price_profit_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='price',
            name='size',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_size', to='mall.size'),
        ),
    ]