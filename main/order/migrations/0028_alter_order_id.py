# Generated by Django 4.0 on 2023-12-05 16:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0027_remove_order_order_id_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
    ]
