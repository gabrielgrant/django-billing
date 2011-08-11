
from billing.processor.api import BillingProcessor

from billing.processor.simple_account.forms import get_billing_details_form
from billing.processor.simple_account.models import has_valid_billing_details

class SimpleAccountBillingProcessor(BillingProcessor):
    has_valid_billing_details = staticmethod(has_valid_billing_details)
    get_billing_details_form = staticmethod(get_billing_details_form)


