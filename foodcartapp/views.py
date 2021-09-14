from django.http import JsonResponse
from django.db import transaction
from django.templatetags.static import static
from rest_framework import status

from .models import Product, OrderItem, OrderDetails
from place.models import Place
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from foodcartapp.utils import fetch_coordinates
from django.conf import settings


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderDetailsSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = OrderDetails
        fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    serializer = OrderDetailsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    customer_order = OrderDetails.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )
    for product in serializer.validated_data['products']:
        OrderItem.objects.create(
            order=customer_order,
            product=product['product'],
            quantity=product['quantity'],
            position_cost=product['product'].price * product['quantity']
        )

    place = Place.objects.get_or_create(
        address=serializer.validated_data['address'],
        lat=fetch_coordinates(settings.YANDEX_GEOCODE_APIKEY, serializer.validated_data['address'])[0],
        lon=fetch_coordinates(settings.YANDEX_GEOCODE_APIKEY, serializer.validated_data['address'])[1],
    )

    order_details = {'id': customer_order.id, **serializer.data, }
    return Response(order_details, status=status.HTTP_200_OK)
