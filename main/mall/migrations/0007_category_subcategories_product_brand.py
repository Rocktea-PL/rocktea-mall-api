# Generated by Django 4.0 on 2023-09-06 22:34

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0006_alter_customuser_associated_domain'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Phone and Tablet', 'Phone and Tablet'), ("Men's Fashion", "Men's Fashion"), ("Women's Fashion", "Women's Fashion"), ('Mobile Accessories', 'Mobile Accessories'), ('Electronics', 'Electronics'), ('Health & Beauty', 'Health & Beauty'), ('Kids', 'Kids'), ('Sporting', 'Sporting'), ('Computing', 'Computing'), ('Groceries', 'Groceries'), ('Video Games', 'Video Games'), ('Home & Office', 'Home & Office')], max_length=18, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubCategories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.fields.CharField, related_name='categories', to='mall.category')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sn', models.IntegerField(unique=True)),
                ('sku', models.CharField(max_length=8, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('quantity', models.IntegerField()),
                ('color', models.CharField(choices=[('Red', 'Red'), ('Yellow', 'Yellow'), ('Blue', 'Blue'), ('Green', 'Green'), ('Orange', 'Orange'), ('Purple', 'Purple'), ('Pink', 'Pink'), ('Brown', 'Brown'), ('Gray', 'Gray'), ('Black', 'Black'), ('White', 'White'), ('Beige', 'Beige'), ('Cyan', 'Cyan'), ('Magenta', 'Magenta'), ('Lavender', 'Lavender'), ('Teal', 'Teal'), ('Navy', 'Navy'), ('Olive', 'Olive'), ('Maroon', 'Maroon'), ('Turquoise', 'Turquoise'), ('Indigo', 'Indigo'), ('Violet', 'Violet'), ('Gold', 'Gold'), ('Silver', 'Silver'), ('Bronze', 'Bronze'), ('Nude', 'Nude'), ('Neutral', 'Neutral'), ('Berge', 'Berge'), ('Ivory', 'Ivory'), ('Metallic', 'Metallic'), ('Grow', 'Grow'), ('Multi', 'Multi'), ('Clear', 'Clear'), ('Burgundy', 'Burgundy'), ('Rose Gold', 'Rose Gold')], max_length=9)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.category')),
            ],
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, unique=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.category', unique=True)),
            ],
        ),
    ]
