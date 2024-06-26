# Generated by Django 4.2 on 2024-05-03 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0034_store_background_color_store_button_color_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='background_color',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='store',
            name='button_color',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='store',
            name='card_elevation',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='store',
            name='card_view',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='store',
            name='color_gradient',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='store',
            name='patterns',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
