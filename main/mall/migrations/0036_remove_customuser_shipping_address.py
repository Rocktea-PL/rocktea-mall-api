# Generated by Django 4.0 on 2023-10-25 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0035_customuser_shipping_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='shipping_address',
        ),
    ]