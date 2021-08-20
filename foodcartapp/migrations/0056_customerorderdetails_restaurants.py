# Generated by Django 3.2 on 2021-08-13 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0055_customerorderdetails_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerorderdetails',
            name='restaurants',
            field=models.ManyToManyField(blank=True, related_name='order', to='foodcartapp.Restaurant', verbose_name='Рестораны'),
        ),
    ]