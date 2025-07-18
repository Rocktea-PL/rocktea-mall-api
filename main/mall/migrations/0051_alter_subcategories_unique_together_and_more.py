# Generated by Django 5.2 on 2025-06-04 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0050_storeproductpricing_created_at_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subcategories',
            unique_together={('category', 'name')},
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['subcategory'], name='product_subcategory_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['producttype'], name='product_producttype_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['brand'], name='product_brand_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_available'], name='product_available_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['upload_status'], name='product_status_idx'),
        ),
        migrations.AddIndex(
            model_name='producttypes',
            index=models.Index(fields=['subcategory'], name='producttypes_subcategory_idx'),
        ),
        migrations.AddIndex(
            model_name='subcategories',
            index=models.Index(fields=['category'], name='subcategories_category_idx'),
        ),
    ]
