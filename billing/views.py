from django.views.generic import TemplateView, FormView
from django.core.urlresolvers import reverse
from django.http import Http404

import billing.loading
import billing.processor
from billing.forms import SubscriptionConfirmationForm
from billing.models import Subscription, ProductType


class BillingOverviewView(TemplateView):
    """
    presents a list/descriptions of the different products on offer
    
    Should display links to the various product pages so users can upgrade
    or downgrade their current subscription.
    """
    template_name = 'billing/overview.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BillingOverviewView, self).get_context_data(**kwargs)
        # Add in a list of all the products
        context['all_products'] = billing.loading.get_products(hidden=True)
        context['public_products'] = billing.loading.get_products()
        billing_account = self.request.user.billing_account
        context['billing_account'] = billing_account
        context['products'] = billing_account.get_visible_products()
        current_product = billing_account.get_current_product_class()
        context['current_product'] = current_product
        return context

class BaseBillingDetailsView(FormView):
    def get_success_url(self):
        return self.request.path
    def form_valid(self, form):
        ba = self.request.user.billing_account

        # let billing processor save details
        form.billing_account = ba
        form.save()

        # do redirect (or do more processing by ignoring return value)
        return super(BaseBillingDetailsView, self).form_valid(form)

class BaseSubscriptionView(BaseBillingDetailsView):
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BaseSubscriptionView, self).get_context_data(**kwargs)
        product = billing.loading.get_product(self.kwargs['product'])
        context['product'] = product
        return context
    def form_valid(self, form):
        response = super(BaseSubscriptionView, self).form_valid(form)

        ba = self.request.user.billing_account

        # create subscription
        ba.subscribe_to_product(self.kwargs['product'])

        # return the redirect
        return response

class SubscriptionConfirmationView(BaseSubscriptionView):
    """
    Confirms the change of subscription when payment info doesn't
    need to be collected. Subscribes user to given product.
    """
    form_class = SubscriptionConfirmationForm
    def get_template_names(self):
        product_name = self.kwargs['product']
        template_names = [
            'billing/subscription_confirmation_%s.html' % product_name,
            'billing/subscription_confirmation.html'
        ]
        return template_names


class BillingDetailsView(BaseBillingDetailsView):
    """
    Displays the user's currently recorded billing details.
    Allows updating of billing details (using the billing details collection
    form supplied by the payment processor) without changing the user's
    subscription.
    """
    template_name = 'billing/details.html'
    def get_form_class(self):
        billing_account = self.request.user.billing_account
        processor = billing_account.get_processor()
        return processor.get_billing_details_form(billing_account)


class SubscriptionBillingDetailsView(BaseSubscriptionView, BillingDetailsView):
    """
    Collects billing details (using the billing details collection form
    supplied by the payment processor) and subscribes user to the given product
    """
    def get_template_names(self):
        product_name = self.kwargs['product']
        template_names = [
            'billing/subscription_billing_details_%s.html' % product_name,
            'billing/subscription_billing_details.html'
        ]
        return template_names

class CurrentSubscriptionView(TemplateView):
    """
    Shown when a user visits the subscription page for their current product
    
    Primarily used when a user has successfully subscribed to a product
    """
    template_name = 'billing/current_subscription.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CurrentSubscriptionView, self).get_context_data(**kwargs)
        cur_sub = self.request.user.billing_account.get_current_subscription()
        context['current_subscription'] = cur_sub
        return context

class BillingHistoryView(TemplateView):
    template_name = 'billing/history.html'
    pass
    

def subscription_view(
    current_subscription_view=CurrentSubscriptionView.as_view(),
    billing_details_view=SubscriptionBillingDetailsView.as_view(),
    confirmation_view=SubscriptionConfirmationView.as_view(),
):
    """
    returns a function to conditionally dispatch a view based on
    a user's current subscription status
    
    If the user is already subscribed to the plan, dispatch the
    current_subscription_view
    
    If the plan requires billing details, and the user doesn't have
    billing details on file (as reported by the processor), then
    dispatch the billing_details_view
    
    Otherwise (if the plan doesn't require billing details, or the
    user already has billing details on file), then dispatch the
    confirmation_view
    """
    def dispatch(request, *args, **kwargs):
        cur_product_cls = request.user.billing_account.get_current_product_class()
        req_product_name = kwargs['product']
        try:
            req_product_cls = billing.loading.get_product(req_product_name)
        except ValueError:
            raise Http404
        if req_product_cls not in request.user.billing_account.get_visible_products():
            raise Http404
        if cur_product_cls == req_product_cls:
            return current_subscription_view(request, *args, **kwargs)
        elif (
            req_product_cls.get_requires_payment_details()
            and not request.user.billing_account.has_valid_billing_details()
        ):
            return billing_details_view(request, *args, **kwargs)
        elif (
            not req_product_cls.get_requires_payment_details()
            or request.user.billing_account.has_valid_billing_details()
        ):
            return confirmation_view(request, *args, **kwargs)
        else:
            raise RuntimeError('Error: null condition should never occur')
    return dispatch

