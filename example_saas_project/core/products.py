from pricing.products import Product
from pricing.features import IntegerFeature
from pricing.features import AllocatedFeature, MeteredFeature
from pricing.feature_pricing import FixedInclusion, FixedUnitPricing
from pricing.manual_intervention import ManualPreApproval, ManualPostApproval

class MySaaSAppAccount(Product):
    class Projects(IntegerFeature):
        def in_use(self, account):
            return Projects.objects.filter(account=account).count()
    
    class StorageSpace(IntegerFeature):
        """ 
        Assume we get hourly ticks that update how much storage is used
        at that moment. If we got real-time updates every time storage
        usage changed, then the billing scheme would be Allocated instead.
        
        """
        def in_use(self, account):
            return get_storage_in_use(account.user)


class GoldPlan(MySaaSAppAccount):
    base_price = 250
    class Projects(MySaaSAppAccount.Projects, AllocatedFeature):
        pricing_scheme=FixedInclusion(included=10)
    class StorageSpace(MySaaSAppAccount.StorageSpace, MeteredFeature):
        pricing_scheme=FixedUnitPricing(unit_price='0.10')


class SilverPlan(MySaaSAppAccount):
    base_price = 75
    class Projects(MySaaSAppAccount.Projects, AllocatedFeature):
        pricing_scheme=FixedInclusion(included=5)
    class StorageSpace(MySaaSAppAccount.StorageSpace, MeteredFeature):
        pricing_scheme=FixedUnitPricing(unit_price='0.15')


class BronzePlan(MySaaSAppAccount):
    base_price = 25
    class Projects(MySaaSAppAccount.Projects, AllocatedFeature):
        pricing_scheme=FixedInclusion(included=2)
    class StorageSpace(MySaaSAppAccount.StorageSpace, MeteredFeature):
        pricing_scheme=FixedUnitPricing(unit_price='0.20')

class FreePlan(MySaaSAppAccount):
    base_price = 0
    class Projects(MySaaSAppAccount.Projects, AllocatedFeature):
        pricing_scheme=FixedInclusion(included=1)
    class StorageSpace(MySaaSAppAccount.StorageSpace, MeteredFeature):
        pricing_scheme=FixedInclusion(included=0)

class SecretPlan(SilverPlan):
    base_price = 10
    manual_intervention = ManualPreApproval

class SecretFreePlan(BronzePlan):
    base_price = 0
    manual_intervention = ManualPreApproval

class EnterprisePlan(GoldPlan):
    manual_intervention = ManualPostApproval

class CustomPlan(GoldPlan):
    manual_intervention = ManualPreApproval
