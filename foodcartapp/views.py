from django.http import JsonResponse
from django.db import transaction
from django.templatetags.static import static
from django.shortcuts import get_object_or_404
from rest_framework import status

from .models import Product, OrderItems, CustomerOrderDetails
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer


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


class OrderItemsSerializer(ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['product', 'quantity']


class CustomerOrderDetailsSerializer(ModelSerializer):
    products = OrderItemsSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = CustomerOrderDetails
        fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    serializer = CustomerOrderDetailsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    customer = CustomerOrderDetails.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )
    for product in serializer.validated_data['products']:
        order_product = get_object_or_404(Product, name=product['product'])
        OrderItems.objects.create(
            user=get_object_or_404(CustomerOrderDetails, id=customer.id),
            product=get_object_or_404(Product, id=product['product'].id),
            quantity=product['quantity'],
            cost=order_product.price * product['quantity']
            )

    order_details = {'id': customer.id}
    order_details.update(serializer.data)
    return Response(order_details, status=status.HTTP_200_OK)


# {"products": [{"product": 4, "quantity": 1}], "firstname": "Иван", "lastname": "Иванов", "phonenumber": "+79148556840", "address": "Москва Фестивальная  д.5 кв.15"}
