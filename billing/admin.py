from billing.models import Account, ProductType, Subscription, SubscriptionApprovalStatus
from django.contrib import admin

from .loading import get_products

class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    can_delete = False
    #exclude = ['product_type']

def subscribe_actions_iter():
    for product in get_products(hidden=True):
        def create_subscribe_action(product):
            def subscribe_action(modeladmin, request, accounts):
                for account in accounts:
                    account.subscribe_to_product(product)
                if len(accounts) == 1:
                    message_bit = '1 user was'
                else:
                    message_bit = '%s users were' % len(accounts)
                message = '%s successfully subscribed to %s' % (message_bit, product.name)
                modeladmin.message_user(request, message)
            subscribe_action.__name__ = 'subscribe_to_%s' % product.name
            return subscribe_action
        yield create_subscribe_action(product)

class AccountAdmin(admin.ModelAdmin):
    search_fields = ['owner__id', 'owner__username', 'owner__email']
    list_display = [
        '__unicode__',
        lambda x: x.get_current_product_class().name,
        lambda x: x.owner.id,
        lambda x: x.owner.username,
        lambda x: x.owner.email,
    ]
    actions = list(subscribe_actions_iter())
    inlines = [SubscriptionInline]
    raw_id_fields = ['owner']

class SubscriptionAdmin(admin.ModelAdmin):
    list_filter = ['product_type']

admin.site.register(Account, AccountAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
