# Generated by Django 4.0 on 2024-01-24 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0010_alter_storeorder_status_assignorder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storeorder',
            name='delivery_code',
            field=models.CharField(max_length=5, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='storeorder',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Enroute', 'Enroute'), ('Delivered', 'Delivered'), ('Returned', 'Returned')], default='Pending', max_length=9, null=True),
        ),
    ]
