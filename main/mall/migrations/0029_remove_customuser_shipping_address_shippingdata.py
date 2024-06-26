# Generated by Django 4.2 on 2024-03-31 16:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0028_alter_productvariant_colors'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='shipping_address',
        ),
        migrations.CreateModel(
            name='ShippingData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=400)),
                ('state', models.CharField(choices=[('ABIA', 'ABIA'), ('ADAMAWA', 'ADAMAWA'), ('AKWA IBOM', 'AKWA IBOM'), ('ANAMBRA', 'ANAMBRA'), ('BAUCHI', 'BAUCHI'), ('BAYELSA', 'BAYELSA'), ('BENUE', 'BENUE'), ('BORNO', 'BORNO'), ('CROSS RIVER', 'CROSS RIVER'), ('DELTA', 'DELTA'), ('EBONYI', 'EBONYI'), ('EDO', 'EDO'), ('EKITI', 'EKITI'), ('ENUGU', 'ENUGU'), ('FCT (ABUJA)', 'FCT (ABUJA)'), ('GOMBE', 'GOMBE'), ('IMO', 'IMO'), ('JIGAWA', 'JIGAWA'), ('KADUNA', 'KADUNA'), ('KANO', 'KANO'), ('KATSINA', 'KATSINA'), ('KEBBI', 'KEBBI'), ('KOGI', 'KOGI'), ('KWARA', 'KWARA'), ('LAGOS', 'LAGOS'), ('NASARAWA', 'NASARAWA'), ('NIGER', 'NIGER'), ('OGUN', 'OGUN'), ('ONDO', 'ONDO'), ('OSUN', 'OSUN'), ('OYO', 'OYO'), ('PLATEAU', 'PLATEAU'), ('RIVERS', 'RIVERS'), ('SOKOTO', 'SOKOTO'), ('TARABA', 'TARABA'), ('YOBE', 'YOBE'), ('ZAMFARA', 'ZAMFARA')], max_length=11)),
                ('lga', models.CharField(choices=[('FCT', 'Abaji'), ('Lagos', 'Agege'), ('Lagos', 'Alimosho'), ('FCT', 'Bwari'), ('Kano', 'Dala'), ('Edo', 'Egor'), ('Rivers', 'Eleme'), ('Enugu', 'Enugu East'), ('Enugu', 'Enugu North'), ('Enugu', 'Enugu South'), ('Lagos', 'Eti Osa'), ('Kano', 'Fagge'), ('FCT', 'Gwagwalada'), ('Kano', 'Gwale'), ('Oyo', 'Ibadan North'), ('Oyo', 'Ibadan North East'), ('Oyo', 'Ibadan South East'), ('Oyo', 'Ibadan South West'), ('Oyo', 'Ido'), ('Lagos', 'Ifako Ijaye'), ('Lagos', 'Ikeja'), ('Kano', 'Kano Municipal'), ('Lagos', 'Kosofe'), ('FCT', 'Kuje'), ('Kano', 'Kumbotso'), ('FCT', 'Kwali'), ('Lagos', 'Lagos Mainland'), ('Lagos', 'Mushin'), ('Lagos', 'Oshodi Isolo'), ('Imo', 'Owerri Municipal'), ('Imo', 'Owerri North'), ('Rivers', 'Port Harcourt'), ('Lagos', 'Shomolu'), ('Lagos', 'Surulere'), ('Kano', 'Tarauni'), ('Kano', 'Ungogo'), ('Rivers', 'Obio/Akpor'), ('Rivers', 'Port-Harcourt'), ('FCT', 'Abuja Municipal Area Council'), ('FCT', 'AMAC')], max_length=39)),
                ('country', models.CharField(max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
