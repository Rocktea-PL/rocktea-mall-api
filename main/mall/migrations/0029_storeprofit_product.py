# Generated by Django 4.0 on 2023-10-24 16:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0028_storeprofit_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeprofit',
            name='product',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.product'),
        ),
    ]
