from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                .filter(availability=True)
                .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=400,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderDetailsQuerySet(models.QuerySet):
    def get_order_with_cost(self):
        order_with_cost = self.annotate(cost=Sum('order_items__position_cost'))
        return order_with_cost


class OrderDetails(models.Model):
    firstname = models.CharField('Имя', max_length=50, db_index=True)
    lastname = models.CharField('Фамилия', max_length=50, db_index=True)
    phonenumber = PhoneNumberField('Телефон', db_index=True)
    address = models.CharField('Адрес', max_length=100, db_index=True)
    status = models.CharField('Статус заказа', max_length=50,
                              choices=[('Обработанный', 'Обработанный'),
                                       ('Необработанный', 'Необработанный')],
                              default='Необработанный',
                              db_index=True)
    payment_method = models.CharField('Платежный метод', max_length=50, blank=True,
                                      choices=[('Наличностью', 'Наличностью'),
                                               ('Электронно', 'Электронно')],
                                      db_index=True)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.SET_NULL,
                                   related_name='orders',
                                   verbose_name='Рестораны',
                                   null=True,
                                   blank=True)
    comments = models.TextField('Комментарии к заказу', blank=True)
    created_at = models.DateTimeField('Время создания', default=timezone.now, db_index=True)
    called_at = models.DateTimeField('Время звонка', blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField('Время доставки', blank=True, null=True, db_index=True)

    objects = OrderDetailsQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        OrderDetails,
        related_name='order_items',
        verbose_name="элементы заказа",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        verbose_name='продукт',
        on_delete=models.CASCADE, )
    quantity = models.IntegerField('Количество', validators=[MinValueValidator(1)])
    position_cost = models.DecimalField(
        'стоимость позиции',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)], null=True)

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f"{self.product.name} {self.order.firstname} {self.order.lastname}"
