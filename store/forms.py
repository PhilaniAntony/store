from django import forms
from django.forms import widgets
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
PAYMENT_CHOICES = (
    ('Stripe', 'Stripe'),
    ('Paypal', 'Paypal'),
)
class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'address',
        'class': 'form-control'
    }))
    appartmentent_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'address2',
        'class': 'form-control'
    }),required=False)
    country = CountryField(blank_label='Select Country').formfield(widget=CountrySelectWidget(attrs={
        'class' : "custom-select d-block w-100"
    }))
    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    same_billing_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField( required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)