from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from apps.user import views
from apps.user.views import ProductListView, Login, logout_view, Sign, ProductCreateView, ProductDetailView, AddToCartView, CartView, remove_from_cart, PreorderView, paymenthandler

urlpatterns = [
    path('', Login.as_view(), name='login_view'),
    path('product_list', ProductListView.as_view(), name='product_list'),
    path('first',views.index),
    path('product_create', ProductCreateView.as_view(), name='product-create'),
    path('product_detail/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('add_to_cart/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/increase/<int:pk>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:pk>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove-from-cart/<int:pk>/', remove_from_cart, name='remove_from_cart'),
    path('preorder/', PreorderView.as_view(), name='preorder'),
    path('login_view/', Login.as_view(), name='login_view'),
    path('sign/', Sign.as_view(), name='signup'),
    path('logout/user/', logout_view, name='logout_user'),
    path('paymenthandler/', paymenthandler, name='paymenthandler'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)