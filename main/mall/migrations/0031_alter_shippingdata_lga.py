# Generated by Django 4.2 on 2024-04-06 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mall', '0030_alter_shippingdata_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shippingdata',
            name='lga',
            field=models.CharField(choices=[('Abaji', 'Abaji'), ('Abaji', 'Abaji'), ('Alimosho', 'Alimosho'), ('Bwari', 'Bwari'), ('Dala', 'Dala'), ('Egor', 'Egor'), ('Eleme', 'Eleme'), ('Enugu East', 'Enugu East'), ('Enugu North', 'Enugu North'), ('Enugu South', 'Enugu South'), ('Eti Osa', 'Eti Osa'), ('Fagge', 'Fagge'), ('Gwagwalada', 'Gwagwalada'), ('Gwale', 'Gwale'), ('Ibadan North', 'Ibadan North'), ('Ibadan North East', 'Ibadan North East'), ('Ibadan South East', 'Ibadan South East'), ('Ibadan South West', 'Ibadan South West'), ('Ido', 'Ido'), ('Ifako Ijaye', 'Ifako Ijaye'), ('Ikeja', 'Ikeja'), ('Kano Municipal', 'Kano Municipal'), ('Kosofe', 'Kosofe'), ('Kuje', 'Kuje'), ('Kumbotso', 'Kumbotso'), ('Kwali', 'Kwali'), ('Lagos Mainland', 'Lagos Mainland'), ('Mushin', 'Mushin'), ('Oshodi Isolo', 'Oshodi Isolo'), ('Owerri Municipal', 'Owerri Municipal'), ('Owerri North', 'Owerri North'), ('Port Harcourt', 'Port Harcourt'), ('Shomolu', 'Shomolu'), ('Surulere', 'Surulere'), ('Tarauni', 'Tarauni'), ('Ungogo', 'Ungogo'), ('Obio/Akpor', 'Obio/Akpor'), ('Port-Harcourt', 'Port-Harcourt'), ('Abuja Municipal Area Council', 'Abuja Municipal Area Council'), ('AMAC', 'AMAC')], max_length=39),
        ),
    ]
