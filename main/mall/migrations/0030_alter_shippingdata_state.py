# Generated by Django 4.2 on 2024-03-31 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0029_remove_customuser_shipping_address_shippingdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shippingdata',
            name='state',
            field=models.CharField(choices=[('ABIA', 'ABIA'), ('ADAMAWA', 'ADAMAWA'), ('AKWA IBOM', 'AKWA IBOM'), ('ANAMBRA', 'ANAMBRA'), ('BAUCHI', 'BAUCHI'), ('BAYELSA', 'BAYELSA'), ('BENUE', 'BENUE'), ('BORNO', 'BORNO'), ('CROSS RIVER', 'CROSS RIVER'), ('DELTA', 'DELTA'), ('EBONYI', 'EBONYI'), ('EDO', 'EDO'), ('EKITI', 'EKITI'), ('ENUGU', 'ENUGU'), ('FCT (ABUJA)', 'FCT (ABUJA)'), ('GOMBE', 'GOMBE'), ('IMO', 'IMO'), ('JIGAWA', 'JIGAWA'), ('KADUNA', 'KADUNA'), ('KANO', 'KANO'), ('KATSINA', 'KATSINA'), ('KEBBI', 'KEBBI'), ('KOGI', 'KOGI'), ('KWARA', 'KWARA'), ('LAGOS', 'LAGOS'), ('NASARAWA', 'NASARAWA'), ('NIGER', 'NIGER'), ('OGUN', 'OGUN'), ('ONDO', 'ONDO'), ('OSUN', 'OSUN'), ('OYO', 'OYO'), ('PLATEAU', 'PLATEAU'), ('RIVERS', 'RIVERS'), ('SOKOTO', 'SOKOTO'), ('TARABA', 'TARABA'), ('YOBE', 'YOBE'), ('ZAMFARA', 'ZAMFARA')], max_length=37),
        ),
    ]
