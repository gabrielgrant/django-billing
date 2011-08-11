
from django.db import models
from django.dispatch import receiver

from billing.signals import ready_for_approval

# account-based immutable processor

class IOUAccount(models.Model):
    billing_account = models.OneToOneField(
        'billing.Account', related_name='simple_processor_iou_account')

class AccountIOU(models.Model):
    iou_account = models.ForeignKey(
        'IOUAccount', related_name='simple_processor_ious')
    has_agreed_to_pay = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created']
        get_latest_by = 'created'
    def __unicode__(self):
        return 'AccountIOU(has_agreed_to_pay=%s)' % self.has_agreed_to_pay
    

def has_valid_billing_details(account):
    try:
        iou_account = account.simple_processor_iou_account
    except IOUAccount.DoesNotExist:
        return False
    return iou_account.simple_processor_ious.latest().has_agreed_to_pay

@receiver(ready_for_approval)
def do_subscription_approval(sender, **kwargs):
    """ `sender` is the subscription instance requiring approval """
    req_payment = sender.get_product_class().get_requires_payment_details()
    if not req_payment or has_valid_billing_details(sender.billing_account):
        status = 'approved'
    else:
        status = 'declined'
    sender.set_current_approval_status(status)
    return status
