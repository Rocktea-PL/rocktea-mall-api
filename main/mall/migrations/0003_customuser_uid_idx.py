# Generated by Django 4.0 on 2023-09-06 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0002_alter_customuser_uid'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['uid'], name='uid_idx'),
        ),
    ]
