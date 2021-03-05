from django.urls import path


#import views
from . import views

app_name = 'store'
urlpatterns = [
    path('', views.HomeView.as_view(), name='homepage'),
    path('product/<slug>/', views.ItemDetailsView.as_view(), name='productpage'),
    path('order-summary/', views.OrderSummary.as_view(), name='order-summary'),
    path('checkout/', views.CheckoutView.as_view(), name='checkoutpage'),
    path('add-to-cart/<slug>/', views.add_to_cart, name='cartview'),
    path('add-item-to-cart/<slug>/', views.add_item_to_cart, name='additemview'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='removeview'),
    path('remove-item-from-cart/<slug>/',
         views.remove_single_item_from_cart, name='removeitemview'),
    path('payment/<payment_option>/', views.PaymentView.as_view(),name='payment'),
    path('add-coupon/', views.add_coupon,name='coupon'),
]
