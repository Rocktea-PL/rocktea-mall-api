# Generated by Django 4.0 on 2024-02-16 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0016_rename_associated_domain_store_domain_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='domain_name',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
    ]