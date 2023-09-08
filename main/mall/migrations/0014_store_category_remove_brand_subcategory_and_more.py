# Generated by Django 4.0 on 2023-09-07 23:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0013_remove_brand_category_brand_subcategory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='category',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.category'),
        ),
        migrations.RemoveField(
            model_name='brand',
            name='subcategory',
        ),
        migrations.AddField(
            model_name='brand',
            name='subcategory',
            field=models.ManyToManyField(null=True, to='mall.SubCategories'),
        ),
    ]