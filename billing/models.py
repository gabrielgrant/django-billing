from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from annoying.fields import AutoOneToOneField
from jsonfield import JSONField
from model_utils import Choices
from model_utils.models import TimeStampedModel

import billing.loading
from billing.processor.utils import router as processor_router
from billing.signals import ready_for_approval

#BILLING_ACCOUNT = getattr(settings, 'BILLING_ACCOUNT', SimpleAccount)

#class BaseAccount(models.Model):
#    """
#    BaseAccount should be subclassed (porbably by a specific payment
#    processor backend) to implement specific account types
#    
#    subclasses must implement a "XX" method, which returns XX.
#    
#    """
#    owner = AutoOneToOneField(User, related_name='billing_account')
#    date_created = models.DateTimeField(auto_now_add=True)
#    content_type = models.ForeignKey(ContentType, editable=False, null=True)

#    # stuff to enable subclassing
#    def save(self):
#        if not self.content_type:
#            if self.__class__ is BaseAccount:
#                raise RuntimeError('BaseAccount must be subclassed')
#            self.content_type = ContentType.objects.get_for_model(self.__class__)
#        super(BaseAccount, self).save()

#    def get_subclass(self):
#        model = self.content_type.model_class()
#        if(model == BaseAccount):
#            raise RuntimeError('BaseAccount must be subclassed')
#        return model

#    def get_subclass_instance(self):
#        return self.get_subclass().objects.get(id=self.id)



class Account(models.Model):
    owner = AutoOneToOneField('auth.User', related_name='billing_account')
    def get_current_subscription(self):
        active_statuses = 'pending', 'approved'
        active_subs = Subscription.objects.  \
            filter_by_current_statuses(active_statuses).  \
            filter(billing_account=self).order_by('-date_created')
        subs = active_subs
        #subs = self.subscriptions.order_by('-date_created')
        r = list(subs[:1])
        if r:
          return r[0]
        return None
    def get_current_product(self):
        pc = self.get_current_product_class()
        if pc:
            return pc()
        #sub = self.get_current_subscription()
        #if sub:
            #return sub.get_product()
            #return ()
        return None
    def get_current_product_class(self):
        sub = self.get_current_subscription()
        if sub:
            return sub.get_product_class()
        elif hasattr(settings, 'BILLING_DEFAULT_PRODUCT'):
            return billing.loading.get_product(settings.BILLING_DEFAULT_PRODUCT)
        return None
    def get_processor(self):
        return processor_router.get_processor_for_account(self)
    def has_valid_billing_details(self):
        return self.get_processor().has_valid_billing_details(self)
    def subscribe_to_product(self, product):
        return Subscription.objects.create_from_product(product, self)
    def get_visible_products(self):
        """ returns the list of products that is visible to the given account """
        all_products = billing.loading.get_products(hidden=True)
        public_products = billing.loading.get_products()
        subscribed_product_types = ProductType.objects  \
            .filter(subscriptions__billing_account=self)  \
            .distinct()
        subscribed_products = set(pt.get_product_class() for pt in subscribed_product_types)
        visible_products = set(public_products).union(subscribed_products)
        return [p for p in all_products if p in visible_products]
    def __unicode__(self):
        return "%s's account" % unicode(self.owner)
    def __repr__(self):
        return "Account(owner=%s)" % repr(self.owner)

class ProductTypeManager(models.Manager):
    def get_for_product(self, product):
        return self.get(name=product.__name__)
    def get_by_natural_key(self, name):
        return self.get(name=name)

class ProductType(models.Model):
    name = models.CharField(max_length=100)
    objects = ProductTypeManager()
    def get_product_class(self):
        return billing.loading.get_product(self.name)
    def __unicode__(self):
        return self.name
    def __repr__(self):
        return 'ProductType(name=%s)' % self.name
    def natural_key(self):
        return (self.name,)

class SubscriptionManager(models.Manager):
    def filter_by_current_statuses(self, statuses):
        """
        returns the subscriptions whose most recent status is
        one of those specified
        """
        
        annotated = self.annotate(
            newest=models.Max('approval_statuses__created'))
        newest_subs = annotated.filter(
            approval_statuses__created=models.F('newest'),
            approval_statuses__status__in=statuses
        )
        return newest_subs
    def filter_by_current_status(self, status):
        """
        returns the subscriptions whose most recent status is that specified
        """
        return self.filter_by_current_statuses([status])
        
    def pending(self):
        return self.filter_by_current_status(status='pending')
    def approved(self):
        return self.filter_by_current_status(status='approved')
    def declined(self):
        return self.filter_by_current_status(status='declined')
    def create_from_product(self, product, billing_account):
        if isinstance(product, basestring):
            name = product
        else:
            name = product.name
        pt = ProductType.objects.get(name=name)
        sub = self.create(billing_account=billing_account, product_type=pt)
        sub.request_approval()

ACTIVE_SUBSCIPRTION_STATUSES = getattr(settings,
    'BILLING_ACTIVE_SUBSCIPRTION_STATUSES', ('pending', 'approved'))  

class Subscription(models.Model):
    APPROVAL_STATUS = Choices('pending', 'approved', 'declined')
    objects = SubscriptionManager()
    billing_account = models.ForeignKey(Account, related_name='subscriptions')
    product_type = models.ForeignKey(
        ProductType, related_name='subscriptions')
    date_created = models.DateTimeField(auto_now_add=True)
    def get_product(self):
        unadjusted_product = self.product_type.get_product_class()
        # this should apply adjustments
        adjustments = Adjustment.objects.filter(subscription=self)
        return unadjusted_product()
    def get_product_class(self):
        return self.product_type.get_product_class()
    def get_current_approval_status(self):
        statuses = self.approval_statuses.order_by('-created')
        r = list(statuses[:1])
        if r:
          return r[0].status
        return None
    def set_current_approval_status(self, status, note=''):
        # Choices is a tuple: (db rep, py identifier, human readable)
        if status not in zip(*self.APPROVAL_STATUS)[1]:
            raise ValueError('"%s" is not a valid status' % status)
        SubscriptionApprovalStatus.objects.create(
            status=status, subscription=self, note=note)
    def is_active(self):
        cur_stat = self.get_current_approval_status()
        return cur_stat in ACTIVE_SUBSCIPRTION_STATUSES
    def request_approval(self):
        ready_for_approval.send(sender=self)
    def __unicode__(self):
        return '%s (%s)' % (self.product_type.name, self.get_current_approval_status())
    def __repr__(self):
        return 'Subscription(product=%s, approval_status=%s)' % (self.product_type.name, self.get_current_approval_status())

@receiver(signals.post_save, sender=Subscription)
def auto_add_subscription_approval_status(instance, created, **kwargs):
    if created:
        instance.set_current_approval_status('pending')
        #SubscriptionApprovalStatus.objects.create(subscription=instance)
        

class SubscriptionApprovalStatus(TimeStampedModel):
    STATUS = Subscription.APPROVAL_STATUS
    status = models.CharField(
        choices=STATUS, default=STATUS.pending, max_length=20)
    subscription = models.ForeignKey(
        Subscription, related_name='approval_statuses')
    note = models.TextField(blank=True)
    def __unicode__(self):
        return 'SubscriptionApprovalStatus(subscription=%s, status=%s)' % (self.subscription, self.status)
    def __repr__(self):
        return self.__unicode__()

class AdjustmentType(models.Model):
    def adjustment_class(self):
        pass

class Adjustment(models.Model):
    adjustment_type = models.ForeignKey(AdjustmentType)
    adjustment_value = JSONField()
    subscription = models.ForeignKey(Subscription)
