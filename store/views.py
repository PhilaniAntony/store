from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import request
from django.shortcuts import redirect, reverse, render, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from core.settings import  stripe_api_key
import stripe
stripe_api_key = stripe_api_key

#import models
from .models import Item, OrderItem, Order, BillingAddress, Payment
from .forms import CheckoutForm

# Create your views here.


class HomeView(ListView):
    model = Item
    paginate_by = 15
    template_name = 'home-page.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        user = self.request.user
        if user:
            qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            context.update({'cart_items': qs[0].items.count()})
        return context


class ItemDetailsView(DetailView):
    model = Item
    template_name = 'product-page.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ItemDetailsView, self).get_context_data(**kwargs)
        qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            context.update({'cart_items': qs[0].items.count()})
        return context



class CheckoutView(LoginRequiredMixin,View):

    def get(self,  *args, **kwargs):
        context = {}
        user = self.request.user
        form = CheckoutForm()
        context['form'] = form
        
        qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            context['cart_items'] = qs[0].items.count()

        return render(self.request, 'checkout-page.html', context)

    def post(self, *args, **kwargs):
        context = {}
        form = CheckoutForm(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address= form.cleaned_data.get('street_address')
                appartmentent_address = form.cleaned_data.get('appartmentent_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                #same_billing_address = form.cleaned_data.get('same_billing_address')
                #save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')

                billing_adrress = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    appartmentent_address=appartmentent_address,
                    country=country,
                    zip=zip
                )
                billing_adrress.save()
                order.billing_address = billing_adrress
                order.save()
                if payment_option == 'Stripe':
                    return redirect('store:payment', payment_option ='stripe')
                elif payment_option == 'Paypal':
                    return redirect('store:payment', payment_option ='paypal')
                else:
                    return redirect('store:checkoutpage')
        except ObjectDoesNotExist:
            return redirect('/')
        
        return redirect('store:checkoutpage')

class PaymentView(View):
    
    def get(self,*rags, **kwargs):
        context = {}
        order = Order.objects.get(user=self.request.user, ordered = False)
        context['order'] = order
        return render(self.request, 'payment.html', context) 

    def post(self,*rags, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered = False)
        amount= int(order.get_total() * 100)
        token =self.request.POST.get('stripeToken')

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
            )
            #create payment
            payment = Payment()
            payment.stripe.charge_id = charge['id']
            payment.user = self.request.user
            payment.amount= amount
            payment.save()

            order.ordered = True
            order.payment = payment
            order.save()
            return redirect("/")
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f'{ err.get("messsage") }')
            return redirect("/")

        except stripe.error.RateLimitError as e:

            messages.error(self.request, 'Rate limit error')
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, 'Inavlid parameter')
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            messages.error(self.request,'Not authenticated' )
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            messages.error(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            messages.error(self.request, "Something went wrong, you were not charged. Please try again")
            return redirect("/")
        except Exception as e:
            # send an email to ourself
            messages.error(self.request,'A serious error occured, we have been notified')


@login_required
def add_to_cart(request, slug):
    # get item
    item = get_object_or_404(Item, slug=slug)

    # check if order-item exist in qs or create one
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)

    # check if orderitem exist in order and get order not completed
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if order_item in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
        else:
            messages.info(request, 'this item was added to the cart')
            order.items.add(order_item)
    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, order_date=order_date)
        order.items.add(order_item)
    return redirect('store:order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        # check if order_item in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            messages.info(request, 'Item was removed to the cart')
            order.items.remove(order_item)
    else:
        messages.info(request, 'Item does not exist in the order')
        return redirect('store:productpage', slug=slug)

    return redirect('store:productpage', slug=slug)


@login_required
def add_item_to_cart(request, slug):
    # get item
    item = get_object_or_404(Item, slug=slug)

    # check if order-item exist in qs or create one
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)

    # check if orderitem exist in order and get order not completed
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if order_item in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()

    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, order_date=order_date)
        order.items.add(order_item)
    return redirect('store:order-summary')


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        # check if order_item in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)

            messages.info(request, 'Item was removed to the cart')
            return redirect('store:order-summary')
    else:
        messages.info(request, 'Item does not exist in the order')
        return redirect('store:productpage', slug=slug)

    return redirect('store:productpage', slug=slug)


class OrderSummary(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
        except ObjectDoesNotExist:
            return redirect('/')
        return render(self.request, 'order_summary.html', context)
