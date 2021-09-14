from geopy import distance

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, OrderDetails
from place.models import Place


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:
        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def get_order_distance(restaurant_address, order_address, places):
    try:
        restaurant_attrs = list(filter(lambda x: (x['address'] == restaurant_address), places))[0]
        order_attrs = list(filter(lambda x: (x['address'] == order_address), places))[0]
        restaurant_coords = restaurant_attrs['lat'], restaurant_attrs['lon']
        order_coords = order_attrs['lat'], order_attrs['lon']
        order_distance = f'{distance.distance(restaurant_coords, order_coords).km:.3f}'
    except TypeError:
        order_distance = 'Неверный адрес доставки'
    return order_distance


def serialize_order(order, places):
    restaurants_in_order = []
    restaurants_in_product = set()
    products_in_order = order.order_items.all()
    for product in products_in_order:
        restaurants = product.product.menu_items.all()
        for restaurant in restaurants:
            if restaurant.availability:
                order_distance = get_order_distance(restaurant.restaurant.address, order.address, places)
                restaurants_in_product.add(((restaurant.restaurant.name.split()[-1]), order_distance))
        restaurants_in_order.append(restaurants_in_product.copy())
        restaurants_in_product.clear()
    unique_restaurants = restaurants_in_order[0]
    for index, _ in enumerate(restaurants_in_order):
        unique_restaurants = unique_restaurants.intersection(restaurants_in_order[index])

    restaurants_in_order = unique_restaurants
    return {
        'id': order.id,
        'status': order.status,
        'restaurants': restaurants_in_order,
        'payment_method': order.payment_method,
        'cost': order.cost,
        'fullname': f'{order.firstname} {order.lastname}',
        'phonenumber': order.phonenumber,
        'comments': order.comments,
        'address': order.address
    }


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    order_items = OrderDetails.objects.get_order_with_cost().\
        filter(status='Необработанный').\
        prefetch_related('order_items__product', 'order_items__product__menu_items__restaurant')
    places = Place.objects.values('address', 'lat', 'lon')
    context = {
        'order_items': [serialize_order(order, places) for order in order_items],
    }

    return render(request, template_name='order_items.html', context=context)
