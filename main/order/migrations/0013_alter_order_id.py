# Generated by Django 4.0 on 2023-11-05 16:48

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0012_alter_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.BigIntegerField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
    ]
