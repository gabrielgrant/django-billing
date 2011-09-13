import billing.models
from billing.models import ProductType
from billing.loading import get_products
from django.db.models import signals
import south.signals

# implementation taken from django.contrib.contenttypes:
# https://github.com/django/django/blob/1.3.X/django/contrib/contenttypes/management.py

def update_producttypes(app, verbosity=2, **kwargs):
    # only do this once, after we're synced
    if app == 'billing' or app == billing.models:
        update_all_producttypes(verbosity, **kwargs)
    else:
        return
    

def update_all_producttypes(verbosity=2, **kwargs):
    
    product_types = list(ProductType.objects.all())
    for product in get_products(hidden=True):
        try:
            pt = ProductType.objects.get(name=product.__name__)
            product_types.remove(pt)
        except ProductType.DoesNotExist:
            pt = ProductType(name=product.__name__)
            pt.save()
            if verbosity >= 2:
                print "Adding product type '%s'" % (pt.name)
    # The presence of any remaining product types means the supplied app has an
    # undefined product. Confirm that the product type is stale before deletion.
    if product_types:
        if kwargs.get('interactive', False):
            prodcut_type_display = '\n'.join(['    %s' % pt.name for pt in product_types])
            ok_to_delete = raw_input("""The following product types are stale and need to be deleted:

%s

Any objects related to these product types by a foreign key will also
be deleted. Are you sure you want to delete these product types?
If you're unsure, answer 'no'.

    Type 'yes' to continue, or 'no' to cancel: """ % product_type_display)
        else:
            ok_to_delete = False

        if ok_to_delete == 'yes':
            for pt in product_types:
                if verbosity >= 2:
                    print "Deleting stale product type '%s'" % pt.name
                pt.delete()
        else:
            if verbosity >= 2:
                print "Stale product types remain."
            

signals.post_syncdb.connect(update_producttypes)
south.signals.post_migrate.connect(update_producttypes)

if __name__ == "__main__":
    update_all_contenttypes()
