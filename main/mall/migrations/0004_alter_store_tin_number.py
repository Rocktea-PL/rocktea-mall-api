# Generated by Django 4.0 on 2023-10-15 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0003_wishlist_cart'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='TIN_number',
            field=models.BigIntegerField(),
        ),
    ]
