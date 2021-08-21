from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True,
        db_index=True
    )
    lat = models.CharField(
        'широта',
        max_length=100,
        blank=True,
    )
    lon = models.CharField(
        'долгота',
        max_length=100,
        blank=True,
    )
    update_date = models.DateTimeField(
        'дата обновления',
        default=timezone.now,
        db_index=True
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.address
