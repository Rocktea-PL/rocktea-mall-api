# Generated by Django 4.0 on 2024-01-11 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0005_alter_servicesbusinessinformation_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('Inappropriate Behavior', 'Inappropriate Behavior'), ('Violating Terms of Service', 'Violating Terms of Service'), ('Shipping and Fulfillment Issues', 'Shipping and Fulfillment Issues'), ('Poor Customer Service', 'Poor Customer Service'), ('Unfair Competition Practices', 'Unfair Competition Practices'), ('Fraudulent Activities', 'Fraudulent Activities')], max_length=31, null=True)),
                ('other', models.CharField(max_length=30, null=True)),
                ('details', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported_user', to='mall.customuser')),
            ],
        ),
    ]
