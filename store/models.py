from django.db import models
from django.conf import settings
from django_countries.fields import CountryField

from django.shortcuts import reverse
from django.contrib.auth.models import User

# Create your models here.
# orderitem

CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('OW', 'Out Wear'),
    ('SW', 'Sports Wear'),
)

LABEL_CHOICES = (
    ('p', 'primary'),
    ('s', 'secondary'),
    ('d', ' danger'),
)


class Item(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(
        default='Lorem ipsum dolor sit amet consectetur adipisicing elit. Et dolor suscipit libero eos atque quia ipsa sint voluptatibus! Beatae sit assumenda asperiores iure at maxime atque repellendus maiores quia sapiente.')
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=1)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    image = models.ImageField(blank=True, null=True)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("store:productpage", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("store:cartview", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        return reverse("store:removeview", kwargs={"slug": self.slug})

    @property
    def get_discount(self):
        product_price = self.price - self.discount_price
        rounded_price = round(product_price, 2)
        return rounded_price

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url 


class OrderItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.quantity} of {self.item.title}'

    def get_total_item_price(self):
        if self.item.discount_price:
            return self.quantity * self.item.get_discount
        else:
            return self.quantity * self.item.price

    def get_amount_saved(self):
        if self.item.discount_price:
            return self.quantity * self.item.discount_price


# order


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    ordered = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    order_date = models.DateTimeField()
    billing_address = models.ForeignKey('BillingAddress',blank=True, null=True, on_delete=models.SET_NULL)
    payment = models.ForeignKey('Payment', blank=True,null=True,on_delete=models.SET_NULL)
    coupon = models.ForeignKey('Coupon', blank=True,null=True,on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.user.username}  '

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        total -= self.coupon.amount
        return total

class BillingAddress (models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    appartmentent_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.email
class  Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True, null=True, on_delete=models.SET_NULL)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

class Coupon (models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()
    def __str__(self):
        return self.code