# Generated by Django 4.0 on 2024-03-19 16:44

import datetime
from django.db import migrations, models
from datetime import timezone

class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0026_alter_buyerbehaviour_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 3, 19, 16, 44, 30, 542719, tzinfo=timezone.utc)),
            preserve_default=False,
        ),
    ]
