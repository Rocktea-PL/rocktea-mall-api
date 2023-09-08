# Generated by Django 4.0 on 2023-09-07 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0012_store_cover_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='brand',
            name='category',
        ),
        migrations.AddField(
            model_name='brand',
            name='subcategory',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.subcategories'),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.brand'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_created=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='product',
            name='on_promo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='subcategory',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.subcategories'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.category'),
        ),
    ]