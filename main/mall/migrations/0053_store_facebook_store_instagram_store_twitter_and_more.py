# Generated by Django 4.0 on 2023-11-20 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0052_remove_accountdetails_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='facebook',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='store',
            name='instagram',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='store',
            name='twitter',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='store',
            name='whatsapp',
            field=models.URLField(null=True),
        ),
    ]
