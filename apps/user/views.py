import razorpay
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, View, CreateView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from pyexpat.errors import messages

from .forms import UserCreateForm, LoginForm, StoreDetails
from .models import Product, User, Cart, CartItem, PreOrder


def index(request):
    return HttpResponse('hello world')



class Sign(CreateView):
    model = User
    template_name = 'register.html'
    form_class = UserCreateForm
    success_url = '/login_view'

    def form_valid(self, form):
        form.instance.password = make_password(form.cleaned_data['password'])
        return super().form_valid(form)

class Login(View):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = 'product_list'

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = User.objects.filter(email=email).first()
        if user is not None:
            print("Enter User")
            authenticated_user = authenticate(request, email=user.email, password=password)
            print(authenticated_user)
            if authenticated_user is not None:
                print("Login Successful")
                login(request, authenticated_user)
                context = {
                    'user_email': authenticated_user.email,
                    'user_first_name': authenticated_user.first_name,
                    'user_last_name': authenticated_user.last_name,
                }
                return redirect('product_list')
            else:
                messages.error(request, 'Authentication failed. Please check your credentials.')
        else:
            print("Invalid Credentials")
            messages.error(request, 'User with this email does not exist.')

        return render(request, self.template_name, {'form': self.form_class})

class HomeView(TemplateView):
    template_name = 'home.html'

def logout_view(request):
    print(11)
    logout(request)
    return redirect('login_view')




# class AddToCartView(View):
#     def post(self, request, pk):
#         cart = Cart.objects.first()  # Simplified: assuming one cart for all users
#         if not cart:
#             cart = Cart.objects.create()
#
#         product = get_object_or_404(Product, pk=pk)
#         cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#
#         if not created:
#             cart_item.quantity += 1
#             cart_item.save()
#
#             return redirect('cart_detail')

# class CartDetailView(DetailView):
#     model = Cart
#     template_name = 'cart_detail.html'
#     context_object_name = 'cart'
#
#     def get_object(self, queryset=None):
#         cart, created = Cart.objects.get_or_create(pk=1)
#         return cart



class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'

class ProductCreateView(CreateView):
    model = Product
    form_class = StoreDetails
    template_name = 'product_form.html'
    success_url = reverse_lazy('product_list')

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'



class AddToCartView(LoginRequiredMixin, CreateView):
    model = CartItem
    fields = []

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return redirect('product_list')

    def get_success_url(self):
        return reverse_lazy('cart')


class CartView(TemplateView):
    template_name = 'cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.get(user=self.request.user)
        cart_items = cart.cartitem_set.all()

        for item in cart_items:
            item.total_price = item.product.price * item.quantity

        context['cart_items'] = cart_items
        context['total_price'] = sum(item.total_price for item in cart_items)
        context['total'] = sum(item.product.price * item.quantity for item in context['cart_items'])
        return context






def increase_quantity(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    item.quantity += 1
    item.save()
    return redirect('cart')

def decrease_quantity(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    return redirect('cart')


def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    item.delete()
    return redirect('cart')


class PreorderView(TemplateView):
    template_name = 'preorder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.get(user=self.request.user)
        cart_items = cart.cartitem_set.all()
        total_price = sum(item.product.price * item.quantity for item in cart_items)

        # Create Razorpay    client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create a Razorpay Order
        razorpay_order = client.order.create({
            "amount": int(total_price * 100),  # Convert amount to paisa
            "currency": "INR",
            "payment_capture": "1"
        })

        context['cart_items'] = cart_items
        context['total_price'] = total_price
        context['total'] = total_price
        context['razorpay_order_id'] = razorpay_order['id']
        context['razorpay_key_id'] = settings.RAZORPAY_KEY_ID
        context['currency'] = "INR"
        context['callback_url'] = "paymenthandler/"  # Replace with your payment handler URL

        return context

    def post(self, request, *args, **kwargs):
        # This method remains the same as your current implementation
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()

        if cart_items.exists():
            for item in cart_items:
                PreOrder.objects.create(
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity
                )
            cart_items.delete()

        return redirect('product_list')


@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        try:
            # Get the payment details from the request
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            # Verify the payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)

            # If verification is successful, update the PreOrder with payment_id
            preorders = PreOrder.objects.filter(user=request.user, payment_id__isnull=True)
            preorders.update(payment_id=payment_id, status='Paid')

            # Redirect to the preorder list page
            return redirect('product_list')

        except:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


class PreOrderListView(ListView):
    model = PreOrder
    template_name = 'preorder_list.html'
    context_object_name = 'preorders'

    def get_queryset(self):
        return PreOrder.objects.filter(user=self.request.user)