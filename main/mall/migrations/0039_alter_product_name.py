# Generated by Django 4.2 on 2024-05-13 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0038_alter_product_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]