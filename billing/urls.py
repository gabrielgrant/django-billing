from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required

from billing.views import BillingOverviewView, subscription_view
from billing.views import BillingHistoryView, BillingDetailsView

urlpatterns = patterns('',
    url(r'^$', login_required(BillingOverviewView.as_view()), name='billing_overview'),
    url(r'^subscription/(?P<product>[\w]+)/$',
        login_required(subscription_view()),
        name='billing_subscription'),
    url(r'^history/$',
        login_required(BillingHistoryView.as_view()),
        name='billing_history'),
    url(r'^details/$',
        login_required(BillingDetailsView.as_view()),
        name='billing_details'),
)
