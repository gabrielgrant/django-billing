from django import template

import billing.loading
from pricing.products import Product

register = template.Library()

@register.filter
def product_change_type(product, user):
    upc = user.billing_account.get_current_product_class()
    if isinstance(product, Product):
        product = type(product)
    if upc:
        products = billing.loading.get_products(hidden=True)
        upc_index = products.index(upc)
        p_index = products.index(product)
        if upc_index < p_index:
            return 'upgrade'
        elif upc_index == p_index:
            return None
        else:
            return 'downgrade'
    else:
        return 'upgrade'
