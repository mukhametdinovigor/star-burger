# Generated by Django 3.2 on 2021-08-11 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_auto_20210812_0007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitems',
            name='price',
        ),
    ]
