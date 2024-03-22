# Generated by Django 4.0 on 2024-03-18 20:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0021_alter_productvariant_colors_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerBehaviour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200, unique=True)),
                ('answer', models.TextField()),
                ('user', models.ForeignKey(limit_choices_to={'is_consumer': True}, on_delete=django.db.models.deletion.CASCADE, to='mall.customuser')),
            ],
        ),
    ]
