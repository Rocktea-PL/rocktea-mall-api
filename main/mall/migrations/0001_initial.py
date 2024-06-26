# Generated by Django 4.0 on 2023-12-12 01:46

import cloudinary_storage.storage
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mall.validator
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.CharField(db_index=True, default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(max_length=7, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(max_length=250)),
                ('last_name', models.CharField(max_length=250)),
                ('contact', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('is_store_owner', models.BooleanField(default=False)),
                ('is_consumer', models.BooleanField(default=False)),
                ('password', models.CharField(max_length=200)),
                ('profile_image', models.FileField(storage=cloudinary_storage.storage.RawMediaCloudinaryStorage, upload_to='')),
                ('shipping_address', models.CharField(max_length=500, null=True)),
                ('type', models.CharField(choices=[('Personal Assistant', 'Personal Assistant'), ('Fashion Designer', 'Fashion Designer'), ('Makeup Artist', 'Makeup Artist')], max_length=18, null=True)),
                ('is_services', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Phone and Tablet', 'Phone and Tablet'), ("Men's Fashion", "Men's Fashion"), ("Women's Fashion", "Women's Fashion"), ('Mobile Accessories', 'Mobile Accessories'), ('Electronics', 'Electronics'), ('Health & Beauty', 'Health & Beauty'), ('Kids', 'Kids'), ('Sporting', 'Sporting'), ('Computing', 'Computing'), ('Groceries', 'Groceries'), ('Video Games', 'Video Games'), ('Home & Office', 'Home & Office')], max_length=18, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='MarketPlace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list_product', models.BooleanField(db_index=True, default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('sku', models.CharField(blank=True, max_length=8, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(null=True)),
                ('quantity', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('on_promo', models.BooleanField(default=False)),
                ('is_available', models.BooleanField(default=True)),
                ('upload_status', models.CharField(choices=[('Approved', 'Approved'), ('Pending', 'Pending'), ('Rejected', 'Rejected')], default='Pending', max_length=8, null=True)),
                ('sales_count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images', models.FileField(storage=cloudinary_storage.storage.RawMediaCloudinaryStorage, upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField(max_length=50, null=True)),
                ('colors', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Red', 'Red'), ('Orange', 'Orange'), ('Yellow', 'Yellow'), ('Green', 'Green'), ('Blue', 'Blue'), ('Purple', 'Purple'), ('Pink', 'Pink'), ('Brown', 'Brown'), ('Gray', 'Gray'), ('Black', 'Black'), ('White', 'White'), ('Cyan', 'Cyan'), ('Magenta', 'Magenta'), ('Lime', 'Lime'), ('Teal', 'Teal'), ('Indigo', 'Indigo'), ('Maroon', 'Maroon'), ('Olive', 'Olive'), ('Navy', 'Navy'), ('Silver', 'Silver')], max_length=20), size=None)),
                ('wholesale_price', models.DecimalField(decimal_places=2, max_digits=11)),
                ('product', models.ManyToManyField(related_name='product_variants', to='mall.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.CharField(db_index=True, default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('TIN_number', models.BigIntegerField(null=True)),
                ('logo', models.FileField(null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage, upload_to='')),
                ('cover_image', models.FileField(null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage, upload_to='')),
                ('year_of_establishment', models.DateField(null=True, validators=[mall.validator.YearValidator])),
                ('associated_domain', models.CharField(max_length=15, null=True)),
                ('theme', models.CharField(max_length=6, null=True)),
                ('facebook', models.URLField(null=True)),
                ('whatsapp', models.URLField(null=True)),
                ('instagram', models.URLField(null=True)),
                ('twitter', models.URLField(null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.category')),
                ('owner', models.OneToOneField(limit_choices_to={'is_store_owner': True}, on_delete=django.db.models.deletion.CASCADE, related_name='owners', to='mall.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.product')),
                ('user', models.ForeignKey(limit_choices_to={'is_consumer': True}, on_delete=django.db.models.deletion.CASCADE, to='mall.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('account_name', models.CharField(max_length=300, null=True)),
                ('pending_balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('nuban', models.CharField(max_length=10, null=True, unique=True)),
                ('bank_code', models.IntegerField(null=True)),
                ('store', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.store')),
            ],
        ),
        migrations.CreateModel(
            name='SubCategories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='mall.category')),
            ],
        ),
        migrations.CreateModel(
            name='StoreProductPricing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('retail_price', models.DecimalField(decimal_places=2, max_digits=11)),
                ('product_variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storeprices', to='mall.productvariant')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.store')),
            ],
        ),
        migrations.CreateModel(
            name='ServicesBusinessInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('contact', models.CharField(max_length=14, unique=True)),
                ('years_of_experience', models.CharField(max_length=15)),
                ('about', models.TextField(max_length=100)),
                ('business_photograph', models.FileField(storage=cloudinary_storage.storage.RawMediaCloudinaryStorage, upload_to='')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='ProductTypes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='producttypes', to='mall.subcategories')),
            ],
        ),
        migrations.AddIndex(
            model_name='productimage',
            index=models.Index(fields=['images'], name='product_images_imagesx'),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.brand'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='category', to='mall.category'),
        ),
        migrations.AddField(
            model_name='product',
            name='images',
            field=models.ManyToManyField(to='mall.ProductImage'),
        ),
        migrations.AddField(
            model_name='product',
            name='producttype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.producttypes'),
        ),
        migrations.AddField(
            model_name='product',
            name='store',
            field=models.ManyToManyField(blank=True, related_name='store_products', to='mall.Store'),
        ),
        migrations.AddField(
            model_name='product',
            name='subcategory',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.subcategories'),
        ),
        migrations.AddField(
            model_name='marketplace',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='mall.product'),
        ),
        migrations.AddField(
            model_name='marketplace',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.store'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['name'], name='category_name_namex'),
        ),
        migrations.AddField(
            model_name='cart',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mall.product'),
        ),
        migrations.AddField(
            model_name='cart',
            name='store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.store'),
        ),
        migrations.AddField(
            model_name='cart',
            name='user',
            field=models.ForeignKey(limit_choices_to={'is_consumer': True}, on_delete=django.db.models.deletion.CASCADE, to='mall.customuser'),
        ),
        migrations.AddField(
            model_name='brand',
            name='producttype',
            field=models.ManyToManyField(to='mall.ProductTypes'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='associated_domain',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mall.store'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AddIndex(
            model_name='subcategories',
            index=models.Index(fields=['name'], name='subcategories_name_namex'),
        ),
        migrations.AddIndex(
            model_name='store',
            index=models.Index(fields=['id'], name='store_id_idx'),
        ),
        migrations.AddIndex(
            model_name='store',
            index=models.Index(fields=['owner'], name='store_owner_ownerx'),
        ),
        migrations.AddIndex(
            model_name='store',
            index=models.Index(fields=['name'], name='store_name_namex'),
        ),
        migrations.AddIndex(
            model_name='producttypes',
            index=models.Index(fields=['name'], name='producttypes_name_namex'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['id'], name='product_id_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sku'], name='product_sku_skux'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='product_name_namex'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category'], name='product_category_categoryx'),
        ),
        migrations.AddIndex(
            model_name='brand',
            index=models.Index(fields=['name'], name='brand_name_namex'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['id'], name='id_idx'),
        ),
    ]
