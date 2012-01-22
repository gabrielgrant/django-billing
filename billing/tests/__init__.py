#!/usr/bin/env python

from django.utils import unittest
from django.test import TestCase
from django.core.management import call_command
from django.core import serializers

JSONSerializer = serializers.get_serializer("json")

from ordereddict import OrderedDict

from billing import loading
from billing.models import *
from billing.processor.simple_account.processor import SimpleAccountBillingProcessor
from billing.processor.simple_account.models import IOUAccount, AccountIOU
from billing.templatetags import billing_tags

from example_saas_project.core import billing as billing_defs
from example_saas_project.core import products as product_defs


class UserTestCase(TestCase):
    fixtures = ['test_users.json']
    def setUp(self):
        from django.contrib.auth.models import User
        self.u = User.objects.create_user(
            username='testuser',
            email='em@il.com', password='pass'
        )
        
    def tearDown(self):
        pass

class LoggedInUserTestCase(UserTestCase):
    def setUp(self):
        super(LoggedInUserTestCase, self).setUp()
        if not self.client.login(username='testuser', password='pass'):
            raise RuntimeError('login failed')

#####  Model tests  #####

class AccountTests(UserTestCase):
    def setUp(self):
        super(AccountTests, self).setUp()
        self.a = Account.objects.create(owner=self.u)
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass
    
    def test_current_subscription_none(self):
        self.assertIsNone(self.a.get_current_subscription())
    def test_current_product_none(self):
        self.assertIsNone(self.a.get_current_product())
    def test_current_product_class_none(self):
        self.assertIsNone(self.a.get_current_product_class())
    def test_has_valid_billing_details_none(self):
        self.assertFalse(self.a.has_valid_billing_details())
    def test_get_processor(self):
        self.assertEqual(self.a.get_processor(), SimpleAccountBillingProcessor)
    def test_subscribe_to_product_by_class(self):
        iou_account = IOUAccount.objects.create(
            billing_account=self.u.billing_account)
        AccountIOU.objects.create(iou_account=iou_account, has_agreed_to_pay=True)
        self.assertIsNone(self.a.get_current_product())
        self.a.subscribe_to_product(billing_defs.GoldPlan)
        self.assertEqual(self.a.get_current_product_class(), billing_defs.GoldPlan)
    def test_subscribe_to_product_by_name(self):
        iou_account = IOUAccount.objects.create(
            billing_account=self.u.billing_account)
        AccountIOU.objects.create(iou_account=iou_account, has_agreed_to_pay=True)
        self.assertIsNone(self.a.get_current_product())
        self.a.subscribe_to_product('GoldPlan')
        self.assertEqual(self.a.get_current_product_class(), billing_defs.GoldPlan)
    def test_subscribe_to_product_declined(self):
        self.assertIsNone(self.a.get_current_product())
        self.a.subscribe_to_product('GoldPlan')
        self.assertEqual(self.a.get_current_product_class(), None)
    def test_get_visible_products(self):
        all_products = [
            billing_defs.FreePlan,
            billing_defs.SecretPlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
        ]
        public_products = [all_products[0]] + all_products[2:]
        self.assertListEqual(self.a.get_visible_products(), public_products)
        self.a.subscribe_to_product(billing_defs.GoldPlan)
        self.assertListEqual(self.a.get_visible_products(), public_products)
        self.a.subscribe_to_product(billing_defs.SecretPlan)
        self.assertListEqual(self.a.get_visible_products(), all_products)
        self.a.subscribe_to_product(billing_defs.GoldPlan)
        self.assertListEqual(self.a.get_visible_products(), all_products)
        self.a.subscribe_to_product(billing_defs.SecretPlan)
        self.assertListEqual(self.a.get_visible_products(), all_products)

class ProductTypeTests(UserTestCase):
    def test_autodiscover(self):
        self.assertEqual(ProductType.objects.count(), 6)
    def test_get_product_class(self):
        cls = ProductType.objects.get(name='GoldPlan').get_product_class()
        self.assertEqual(cls, billing_defs.GoldPlan)
    def test_get_by_nautral_key(self):
        self.assertEqual(ProductType.objects.get_by_natural_key('GoldPlan').name, 'GoldPlan')
    def test_natural_key(self):
        self.assertEqual(ProductType.objects.get(name='GoldPlan').natural_key(), ('GoldPlan',))
    def test_serialization_deserialization_natural(self):
        serializer = JSONSerializer()
        Subscription.objects.create_from_product(
            billing_defs.GoldPlan, self.u.billing_account)
        s = serializer.serialize(Subscription.objects.all(), use_natural_keys=True)
        deserialized = list(serializers.deserialize('json', s))[0]
        self.assertEqual(deserialized.object, Subscription.objects.get())

class SubscriptionManagerTests(UserTestCase):
    def setUp(self):
        super(SubscriptionManagerTests, self).setUp()
        gold_pt = ProductType.objects.get(name='GoldPlan')
        silver_pt = ProductType.objects.get(name='SilverPlan')
        self.sub1 = Subscription.objects.create(
            product_type=gold_pt, billing_account=self.u.billing_account)
        self.sub2 = Subscription.objects.create(
            product_type=silver_pt, billing_account=self.u.billing_account)
        self.stat1_1 = SubscriptionApprovalStatus.objects.create(
            subscription=self.sub1, status='declined')
        self.stat1_2 = SubscriptionApprovalStatus.objects.create(
            subscription=self.sub1)
        self.stat2_1 = SubscriptionApprovalStatus.objects.create(
            subscription=self.sub2)
        self.stat2_2 = SubscriptionApprovalStatus.objects.create(
            subscription=self.sub2, status='approved')
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass
    
    def test_filter_by_current_status(self):
        self.assertIn(self.sub1, Subscription.objects.pending())
        self.assertNotIn(self.sub1, Subscription.objects.approved())
        self.assertNotIn(self.sub1, Subscription.objects.declined())
        self.assertIn(self.sub2, Subscription.objects.approved())
        self.assertNotIn(self.sub2, Subscription.objects.pending())
        self.assertNotIn(self.sub2, Subscription.objects.declined())
    def test_create_from_product_class(self):
        iou_account = IOUAccount.objects.create(
            billing_account=self.u.billing_account)
        AccountIOU.objects.create(iou_account=iou_account, has_agreed_to_pay=True)
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.SilverPlan)
        Subscription.objects.create_from_product(
            billing_defs.GoldPlan, self.u.billing_account)
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.GoldPlan)
    def test_create_from_product_name(self):
        iou_account = IOUAccount.objects.create(
            billing_account=self.u.billing_account)
        AccountIOU.objects.create(iou_account=iou_account, has_agreed_to_pay=True)
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.SilverPlan)
        Subscription.objects.create_from_product(
            'GoldPlan', self.u.billing_account)
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.GoldPlan)
    def test_create_from_product_declined(self):
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.SilverPlan)
        Subscription.objects.create_from_product(
            'GoldPlan', self.u.billing_account)
        self.assertEqual(
            self.u.billing_account.get_current_product_class(),
            billing_defs.SilverPlan)

class SubscriptionTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass

class DefaultProductTests(UserTestCase):
    def setUp(self):
        try:
            self.old_default_product = settings.DEFAULT_PRODUCT
        except AttributeError:
            pass
        settings.BILLING_DEFAULT_PRODUCT = 'GoldPlan'
        super(DefaultProductTests, self).setUp()

    def tearDown(self):
        del settings.BILLING_DEFAULT_PRODUCT
        try:
            settings.BILLING_DEFAULT_PRODUCT = self.old_default_product
        except AttributeError:
            pass
        super(DefaultProductTests, self).tearDown()

    def test_default_product(self):
        pc = self.u.billing_account.get_current_product_class()
        self.assertIs(pc, billing_defs.GoldPlan)
        p = self.u.billing_account.get_current_product()
        self.assertIsInstance(p, billing_defs.GoldPlan)


class AdjustmentTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass

class CacheTests(TestCase):
    def setUp(self):
        super(CacheTests, self).setUp()
        self._old_products = loading.product_cache
    def tearDown(self):
        super(CacheTests, self).tearDown()
        loading.product_cache = self._old_products
        
    def test_get_product(self):
        self.assertEqual(loading.get_product('GoldPlan'), billing_defs.GoldPlan)
    def test_get_products(self):
        plans = set([
            billing_defs.GoldPlan,
            billing_defs.SilverPlan,
            billing_defs.BronzePlan,
            billing_defs.FreePlan,
        ])
        self.assertSetEqual(set(loading.get_products()), plans)
    def test_get_for_product(self):
        self.assertEqual(
            ProductType.objects.get(name='GoldPlan'),
            ProductType.objects.get_for_product(billing_defs.GoldPlan),
        )
    def test_get_product(self):
        pt = ProductType.objects.get_for_product(billing_defs.GoldPlan)
        self.assertEqual(pt.get_product_class(), billing_defs.GoldPlan)
    def test_populate_product_cache_billing_defs(self):
        BILLING_PRODUCTS = 'example_saas_project.core.billing'
        loading.product_cache = loading.populate_product_cache(
            products=BILLING_PRODUCTS,
        )
        plans = [
            billing_defs.SecretFreePlan,
            billing_defs.FreePlan,
            billing_defs.SecretPlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
        ]
        self.assertListEqual(plans, loading.get_products(hidden=True))
    def test_populate_product_cache_flat_list(self):
        BILLING_PRODUCTS = [
            'example_saas_project.core.products.FreePlan',
            'example_saas_project.core.products.BronzePlan',
            'example_saas_project.core.products.SilverPlan',
            'example_saas_project.core.products.GoldPlan',
            'example_saas_project.core.products.CustomPlan',
            'example_saas_project.core.products.SecretPlan',
            'example_saas_project.core.products.EnterprisePlan',
        ]
        BILLING_DEFINITIONS = ()
        loading.product_cache = loading.populate_product_cache(
            products=BILLING_PRODUCTS,
        )
        plans = [
            billing_defs.FreePlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
            product_defs.CustomPlan,
            product_defs.SecretPlan,
            product_defs.EnterprisePlan,
        ]
        self.assertListEqual(plans, loading.get_products(hidden=True))
    def test_populate_product_cache_module_list(self):
        BILLING_PRODUCTS = ('example_saas_project.core.products', [
            'FreePlan',
            'BronzePlan',
            'SilverPlan',
            'GoldPlan',
            'CustomPlan',
            'SecretPlan',
            'EnterprisePlan',
        ])
        BILLING_DEFINITIONS = ()
        loading.product_cache = loading.populate_product_cache(
            products=BILLING_PRODUCTS,
        )
        plans = [
            billing_defs.FreePlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
            product_defs.CustomPlan,
            product_defs.SecretPlan,
            product_defs.EnterprisePlan,
        ]
        self.assertListEqual(plans, loading.get_products(hidden=True))

class AllProductsTestCase(TestCase):
    def setUp(self):
        super(AllProductsTestCase, self).setUp()
        self._old_products = loading.product_cache
        loading.product_cache = OrderedDict(zip(
        [
            'FreePlan',
            'BronzePlan',
            'SilverPlan',
            'GoldPlan',
            'CustomPlan',
            'SecretPlan',
            'EnterprisePlan',
        ],
        [
            billing_defs.FreePlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
            product_defs.CustomPlan,
            product_defs.SecretPlan,
            product_defs.EnterprisePlan,
        ]))
    def tearDown(self):
        loading.product_cache = self._old_products

class HiddenProductTests(AllProductsTestCase):
    def test_get_products(self):
        self.assertNotIn(product_defs.SecretPlan, loading.get_products())
        self.assertIn(product_defs.SecretPlan, loading.get_products(hidden=True))
    def test_producttype(self):
        billing.management.update_all_producttypes(verbosity=0)
        pt = ProductType.objects.get_for_product(product_defs.SecretPlan)
        self.assertEqual(pt.get_product_class(), product_defs.SecretPlan)


########  View tests  #############

class BaseViewTestCase(LoggedInUserTestCase):
    urls = 'billing.urls'

class BillingOverviewViewTests(BaseViewTestCase):
    def test_products(self):
        r = self.client.get('/')
        products = [
            billing_defs.FreePlan,
            billing_defs.BronzePlan,
            billing_defs.SilverPlan,
            billing_defs.GoldPlan,
        ]
        self.assertListEqual(list(r.context['products']), list(products))
        
class SubscriptionViewTests(BaseViewTestCase):
    def test_dispatch_not_logged_in(self):
        from django.contrib.auth.models import AnonymousUser
        self.client.logout()
        r = self.client.get('/subscription/GoldPlan/')
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/subscription/GoldPlan/', follow=True)
        self.assertEqual(r.request['PATH_INFO'], '/accounts/login/')

    def test_dispatch_non_existent_plan(self):
        r = self.client.get('/subscription/NonExistentPlan/')
        self.assertEqual(r.status_code, 404)

    def test_dispatch_current_plan(self):
        pt = ProductType.objects.get(name='GoldPlan')
        Subscription.objects.create(
            product_type=pt, billing_account=self.u.billing_account)
        r = self.client.get('/subscription/GoldPlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/current_subscription.html', template_names)
        r = self.client.post('/subscription/GoldPlan/', {})
        from django.http import HttpResponseNotAllowed
        self.assertIsInstance(r, HttpResponseNotAllowed)

    def test_dispatch_billing_details_required_present(self):
        iou_account = IOUAccount.objects.create(
            billing_account=self.u.billing_account)
        AccountIOU.objects.create(iou_account=iou_account, has_agreed_to_pay=True)
        r = self.client.get('/subscription/GoldPlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/subscription_confirmation.html', template_names)
        r = self.client.post('/subscription/GoldPlan/', {}, follow=True)
        self.assertEqual(r.status_code, 200)
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertEqual(cur_prod, billing_defs.GoldPlan)

    def test_dispatch_billing_details_required_not_present_declined(self):
        r = self.client.get('/subscription/GoldPlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/subscription_billing_details.html', template_names)
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertIsNone(cur_prod)
        r = self.client.post('/subscription/GoldPlan/', {'has_agreed_to_pay': False}, follow=True)
        self.assertEqual(r.status_code, 200)
        # the subscription should be declined, so it shouldn't be
        # considered current (if it was just pending, it would be current)
        cur_sub = self.u.billing_account.get_current_subscription()
        self.assertIsNone(cur_sub)
        cur_prod = self.u.billing_account.get_current_product_class() 
        self.assertNotEqual(cur_prod, billing_defs.GoldPlan)
        self.assertIsNone(cur_prod)

    def test_dispatch_billing_details_required_not_present_approved(self):
        r = self.client.get('/subscription/GoldPlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/subscription_billing_details.html', template_names)
        # submit with valid details
        r = self.client.post('/subscription/GoldPlan/', {'has_agreed_to_pay': True}, follow=True)
        self.assertEqual(r.status_code, 200)
        prod_cls = self.u.billing_account.get_current_product_class()
        cur_sub = self.u.billing_account.get_current_subscription()
        self.assertIsNotNone(cur_sub)
        cur_prod = self.u.billing_account.get_current_product_class() 
        self.assertEqual(cur_prod, billing_defs.GoldPlan)

    def test_dispatch_billing_details_not_required_present(self):
        r = self.client.get('/subscription/FreePlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/subscription_confirmation.html', template_names)
        r = self.client.post('/subscription/FreePlan/', follow=True)
        self.assertEqual(r.status_code, 200)
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertEqual(cur_prod, billing_defs.FreePlan)

    def test_dispatch_billing_details_not_required_not_present(self):
        r = self.client.get('/subscription/FreePlan/')
        self.assertEqual(r.status_code, 200)
        template_names = [t.name for t in r.templates]
        self.assertIn('billing/subscription_confirmation.html', template_names)
        r = self.client.post('/subscription/FreePlan/', follow=True)
        self.assertEqual(r.status_code, 200)
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertEqual(cur_prod, billing_defs.FreePlan)

    def test_subscribe_to_hidden_product(self):
        r = self.client.get('/subscription/SecretPlan/')
        self.assertEqual(r.status_code, 404)

    def test_resubscribe_to_hidden_product(self):
        self.u.billing_account.subscribe_to_product('SecretPlan')
        r = self.client.get('/subscription/SecretPlan/')
        self.assertEqual(r.status_code, 200)

class BillingHistoryViewTests(BaseViewTestCase):
    def test_fetch(self):
        r = self.client.get('/history/')
        self.assertEqual(r.status_code, 200)

class BillingDetailsViewTests(BaseViewTestCase):
    def test_products_asc_desc(self):
        r = self.client.get('/details/')
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/details/', {'has_agreed_to_pay': True}, follow=True)
        self.assertEqual(r.status_code, 200)

###  Template Tag Tests  ###

class ProductChangeTypeTests(UserTestCase):
    def test_init(self):
        self.assertEqual(
            billing_tags.product_change_type(billing_defs.FreePlan, self.u),
            'upgrade',
        )

class ProcessorTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass

### Management Command Tests ###

class SubscribeCommandTest(UserTestCase):
    def test_subscribe_by_id(self):
        call_command('subscribe_user_to_product', 'testuser', 'SecretFreePlan')
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertEqual(cur_prod, billing_defs.SecretFreePlan)
    def test_subscribe_by_username(self):
        call_command('subscribe_user_to_product', '1', 'SecretFreePlan')
        cur_prod = self.u.billing_account.get_current_product_class()
        self.assertEqual(cur_prod, billing_defs.SecretFreePlan)
    def test_list_plans(self):
        call_command('subscribe_user_to_product')

def main():
    unittest.main()

if __name__ == '__main__':
    main()
