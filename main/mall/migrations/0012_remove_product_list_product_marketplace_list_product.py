# Generated by Django 4.0 on 2023-10-17 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0011_alter_product_list_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='list_product',
        ),
        migrations.AddField(
            model_name='marketplace',
            name='list_product',
            field=models.BooleanField(default=False),
        ),
    ]