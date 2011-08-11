#!/usr/bin/env python

from django.utils import unittest
from django.test import TestCase

from billing import loading
from billing.models import *
from billing.processor.simple_account.processor import SimpleAccountBillingProcessor
from billing.processor.simple_account.models import IOUAccount, AccountIOU

from example_saas_project.core import billing as billing_defs


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
        self.a = Account(owner=self.u)
        
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


class ProductTypeTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_autodiscover(self):
        self.assertEqual(ProductType.objects.count(), 4)
    def test_get_product_class(self):
        cls = ProductType.objects.get(name='GoldPlan').get_product_class()
        self.assertEqual(cls, billing_defs.GoldPlan)

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
        

class SubscriptionTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass


class AdjustmentTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass

class CacheTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
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


########  View tests  #############

class BaseViewTestCase(LoggedInUserTestCase):
    urls = 'billing.urls'

class BillingOverviewViewTests(BaseViewTestCase):
    def test_products_asc_desc(self):
        r = self.client.get('/')
        products_desc = [
            billing_defs.GoldPlan,
            billing_defs.SilverPlan,
            billing_defs.BronzePlan,
            billing_defs.FreePlan,
        ]
        products_asc = reversed(products_desc)
        self.assertListEqual(list(r.context['products_asc']), list(products_asc))
        self.assertListEqual(list(r.context['products_desc']), list(products_desc))
        
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

class BillingHistoryViewTests(BaseViewTestCase):
    def test_fetch(self):
        r = self.client.get('/history/')
        self.assertEqual(r.status_code, 200)

class BillingDetailsViewTests(BaseViewTestCase):
    def test_products_asc_desc(self):
        r = self.client.get('/details/')
        self.assertEqual(r.status_code, 200)
        

class ProcessorTests(TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_init(self):
        pass

def main():
    unittest.main()

if __name__ == '__main__':
    main()
