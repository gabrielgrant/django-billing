django-billing is a simple, generic, plans, pricing and recurring billing
app. It enforces quotas and tracks pre-paid and usage-based features.

Quick Start
===========

There are four steps needed to get started:

1. Install django-billing
2. Plug in a billing processor
3. Define your products
4. Create your templates


1. Installation
---------------

1. pip install django-billing
2. set up the dependencies
3. add `billing` to your list of installed apps
4. run ``python manage.py migrate billing``


2. Billing Processors
---------------------

While django-billing collects all the information needed to bill
customers, it doesn't take a stance on how payments should be collected.
django-billing delegates responsibility for actually charging a customer
to a billing processor. Individual billing processors interface with
different payment collection gateways to actually collect money.

Usually you will just need to install a billing processor by adding it
into the BILLING_PROCESSORS dict in your settings.py

The example project, for instance, has this declaration in it's settings.py::

    BILLING_PROCESSORS = {
        'default': 'billing.processor.simple_account.processor.SimpleAccountBillingProcessor',
    }

For more details see the section on billing processors below.

3. Defining Products
--------------------

Products are what your customers subscribe to, and are defined as
classes (in a similar manner to Django models).

A Product class is used for three puposes:

1. to check the usage of a given feature
2. to enforce limits upon the usage of features
3. to calculate information for invoices

For example, in the example project shipped with django-billing,
there is a base definition 

They are defined as a collection of features (each of which is
composed of a value and a provisioning scheme) along with
certain details about usage limits and pricing.

django-billing relies on python-pricing to set up the
pricing model.

products should be defined in a `products.py` file

An example of defining products can be seen in
example_saas_project/core/products.py

Since products are often created by class hierarchies, only those products
which you wish to be subscribable should be imported into a billing.py

Point to this billing definitions module with ``BILLING_DEFINITIONS``
in settings.py. In the example, the billing definitions are
in example_saas_project/core/billing.py, so in settings.py, we've added::

    BILLING_DEFINITIONS = 'example_saas_project.core.billing'


4. Templates
------------

You need to define a number of templates. There are examples in
example_saas_project/core/templates/billing

billing/current_subscription.html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO


billing/details.html
^^^^^^^^^^^^^^^^^^^^

TODO


billing/history.html
^^^^^^^^^^^^^^^^^^^^

TODO


billing/overview.html
^^^^^^^^^^^^^^^^^^^^^

TODO


billing/subscription_billing_details.html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO


billing/subscription_confirmation.html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO


Motivation
==========

A few years ago, I had a side project that I was ready to launch as a small business. All I needed to do was figure out how to charge for it. Turns out billing systems are hard to build.

But pretty much every company needs one, so a number of SaaS companies have sprung up recently to help handle recurring payments. Unfortunately they only deal with actually issuing a charge. Tracking usage, and determining whether a user has permission to perform an action in the app (possibly based on their usage-to-date or their plan level) is still left up to the app developer.

Because this information is so tightly linked with the app itself, it does make sense to keep this functionality within the app rather than in a third-party service, but it doesn't make sense for everyone to reimplement it themselves.

Ideally, by making it easier to implement a pricing model, django-billing can help smaller projects close the time gap between first creating value for users and actually capturing some of that value for themselves.


Billing Processors
==================

A billing processor is a class that provides a one method and one attribute

has_valid_billing_details(account)

Returns whether the given billing account has valid billing details
registered with the processor.

billing_details_creation_form

A Django form which collects the details needed to bill an account. This form
should have a `save()` method which saves the billing details. This method
may assume that the account for which details are being submitted is stored
in the `billing_account` property.

Additionally, any urls in the processor's urls.py will be mapped into the
billing url space at '/billing/processors/{{ processor_name }}/...'

This can be useful for webhooks callbacks from payment processesor systems.

Writing a Billing Processor
---------------------------

TODO


Processor Routers
=================

A billing processor router is a class that provides a single method:

get_processor_for_account(account)

Suggests the billing processor that should be used for the given account.

Returns None if there is no suggestion

Using Routers
-------------

Billing processor routers are installed using the BILLING_PROCESSOR_ROUTERS
setting. This setting defines a list of class names, each specifying a
router that should be used by the master router (`billing.processor.router`)

The master router is used by django-billing to decide which processor to use.
Whenever an operation needs to perform an operation using a processor, it
consults the master router, which tries each registered router, in turn,
until a processor suggestion is found. If no suggestion is found, the
master router yields the `default` router.

This architecture/API is very much inspired by Django's database routers

Management Commands
===================

django-billing provides the 'subscribe_user_to_product' management command
to manually subscribe a user. This is especially useful when providing
products which require manual pre-approval (i.e. products to which the user
should not be able to subscribe themselves).
