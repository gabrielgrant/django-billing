
class BillingProcessor(object):
    def get_billing_details_form(self, billing_account):
        return self.billing_details_form
    def has_valid_billing_details(self):
        raise NotImplementedError('has_valid_billing_details() must be over-ridden by subclasses')
