from django.conf import settings

from ordereddict import OrderedDict

from pricing.products import Product
from pricing.manual_intervention import ManualPreApproval
#from billing.adjustments import Adjustment

def import_item(x):
    mod_name, cls_name = x.rsplit('.', 1)
    return from_x_import_y(mod_name, cls_name)

def from_x_import_y(x, y):
    # from mod_name import cls_name
    module = __import__(x, fromlist=x.rsplit('.', 1)[0])
    return getattr(module, y)


adjustments_cache = {}

def collect_products_from_modules(modules):
    products = []
    # populate the cache
    if isinstance(modules, basestring):
        modules = (modules,)
    for module_name in modules:
        mod = __import__(module_name, fromlist=module_name.rsplit('.', 1)[0])
        for name, obj in mod.__dict__.items():
            if isinstance(obj, type):
                if issubclass(obj, Product):
                    products.append(obj)
        #        if issubclass(obj, Adjustment):
        #            adjustment_cache[name] = obj
    return products

BILLING_DEFINITIONS = getattr(settings, 'BILLING_DEFINITIONS', ())
BILLING_PRODUCTS = getattr(settings, 'BILLING_PRODUCTS', None)

def populate_product_cache(products=BILLING_PRODUCTS):
    """ returns the populated cache using products as defined in settings.py

    If defined, products must be one of:
        a list of product classes
        a (base_module, [product_class]) tuple
        a module containing product classes
    """
    if not products:
        product_classes = []
    elif isinstance(products, basestring):
        # we have a module containing products
        product_classes = collect_products_from_modules(products)
        product_classes.sort(key=lambda x: x.base_price)
    elif all(isinstance(i, basestring) for i in products):
        # we have a list of products
        product_classes = [import_item(p) for p in products]
    elif len(products) == 2:
        base_module, classes = products
        product_classes = [from_x_import_y(base_module, cls) for cls in classes]
    else:
        raise ValueError("""Invalid value for "product"
        If defined, products must be one of:
            a list of product classes
            a (base_module, [product_class]) tuple
            a module containing product classes
        """)
    return OrderedDict((pc.name, pc) for pc in product_classes)

product_cache = populate_product_cache()

def get_product(name):
    try:
        return product_cache[name]
    except KeyError:
        raise ValueError('"%s" is not a valid product name' % name)

#def get_adjustment(name):
#    return adjustments_cache[name]

def get_products(hidden=False):
    def is_hidden(product):
        return (not hidden) and (p.manual_intervention is ManualPreApproval)
    return [p for p in product_cache.values() if not is_hidden(p)]


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

