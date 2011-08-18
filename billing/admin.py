from billing.models import Account, ProductType, Subscription, SubscriptionApprovalStatus
from django.contrib import admin

admin.site.register(Account)
admin.site.register(ProductType)
admin.site.register(Subscription)
