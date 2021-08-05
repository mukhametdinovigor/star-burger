from django.http import JsonResponse
from django.templatetags.static import static
from django.shortcuts import get_object_or_404

from .models import Product, OrderItems, CustomerDetails
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status



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


@api_view(['POST'])
def register_order(request):
    try:
        customer_order = request.data
        if not isinstance(customer_order['products'], list) or not customer_order['products']:
            return Response({
                'error': 'product key is not presented or not list',
            }, status=status.HTTP_400_BAD_REQUEST)
        customer = CustomerDetails.objects.create(
            first_name=customer_order['firstname'],
            last_name=customer_order['lastname'],
            phone_number=customer_order['phonenumber'],
            address=customer_order['address']
        )
        for product in customer_order['products']:
            OrderItems.objects.create(
                user=get_object_or_404(CustomerDetails, id=customer.id),
                product=get_object_or_404(Product, id=product['product']),
                quantity=product['quantity']
            )

        return Response({'pam pam': 'product presented in list'}, status=status.HTTP_200_OK)
    except KeyError:
        return Response({
            'error': 'product key is not presented or not list',
        }, status=status.HTTP_400_BAD_REQUEST)


# {"products": [{"product": 4, "quantity": 1}], "firstname": "Иван", "lastname": "Иванов", "phonenumber": "+79148556840", "address": "Москва Фестивальная  д.5 кв.15"}
