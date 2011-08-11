from django.conf import settings

from pricing.products import Product
#from billing.adjustments import Adjustment

def import_item(x):
    mod_name, cls_name = x.rsplit('.', 1)
    return from_x_import_y(mod_name, cls_name)

def from_x_import_y(x, y):
    # from mod_name import cls_name
    module = __import__(x, fromlist=x.rsplit('.', 1)[0])
    return getattr(module, y)

product_cache = {}
adjustments_cache = {}

# populate the cache
BILLING_DEFINITIONS = getattr(settings, 'BILLING_DEFINITIONS', ())
if isinstance(BILLING_DEFINITIONS, basestring):
    BILLING_DEFINITIONS = (BILLING_DEFINITIONS,)
for module_name in BILLING_DEFINITIONS:
    mod = __import__(module_name, fromlist=module_name.rsplit('.', 1)[0])
    for name, obj in mod.__dict__.items():
        if isinstance(obj, type):
            if issubclass(obj, Product):
                product_cache[name] = obj
    #        if issubclass(obj, Adjustment):
    #            adjustment_cache[name] = obj

def get_product(name):
    try:
        return product_cache[name]
    except KeyError:
        raise ValueError('"%s" is not a valid product name' % name)

#def get_adjustment(name):
#    return adjustments_cache[name]

def get_products():
    return product_cache.values()


# load the billing processors
BILLING_PROCESSORS = getattr(settings, 'BILLING_PROCESSORS', {})

processor_cache = {}

for k,v in BILLING_PROCESSORS.items():
    processor_cache[k] = import_item(v)

def get_processor(name):
    try:
        return processor_cache[name]
    except KeyError:
        raise ValueError('"%s" is not a valid processor name' % name)

