from django.conf import settings

from billing.loading import get_processor, import_item

__all__ = ('router',)

class BaseProcessorRouter(object):
    def get_processor_for_account(self, account):
        raise NotImplementedError(
            'get_processor_for_account() should be implemented by subclass')

class MasterProcessorRouter(BaseProcessorRouter):
    def __init__(self, router_list):
        self.routers = []
        for pr in BILLING_PROCESSOR_ROUTERS:
            routers.append(import_item(pr))
    def get_processor_for_account(self, account):
        return get_processor(self.get_processor_name_for_account(account))
    def get_processor_name_for_account(self, account):
        chosen_processor = None
        for router in self.routers:
            try:
                method = router.get_processor_for_account
            except AttributeError:
                pass
            else:
                chosen_processor = method(account)
                if chosen_processor:
                    return chosen_processor
        return 'default'


# load the billing processor routers
BILLING_PROCESSOR_ROUTERS = getattr(settings, 'BILLING_PROCESSOR_ROUTERS', ())

router = MasterProcessorRouter(BILLING_PROCESSOR_ROUTERS)
