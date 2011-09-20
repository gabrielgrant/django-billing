from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from billing.loading import get_products
from pricing.manual_intervention import ManualPreApproval

class Command(BaseCommand):
    help = "Subscribes the given user to a product.\n"  \
    "Lists available products if no arguments are given"
    args = "<userid|username> <product_name>"

    def handle(self, *args, **options):
        if len(args) == 0:
            # show list of plans
            def get_plan_str(p):
                hidden = p.manual_intervention is ManualPreApproval
                return '%s%s' % (p.name, ' (hidden)' if hidden else '')
            plan_strs = [get_plan_str(p) for p in get_products(hidden=True)]
            self.stdout.write(
                '\nAvailable plans:\n\n%s' %
                '\n'.join(plan_strs)
            )
            self.stdout.write('\n\n\nFor full help, use --help\n\n')
            return
        elif len(args) != 2:
            raise CommandError(
                'Exactly two arguments are needed: a user and a product')
        userarg, product_name = args
        try:
            user_by_name = User.objects.get(username=userarg)
        except User.DoesNotExist:
            user_by_name = None
        try:
            userid = int(userarg)
        except ValueError:
            userid = None
        try:
            user_by_id = User.objects.get(id=userid)
        except User.DoesNotExist:
            user_by_id = None
        if user_by_name is None and user_by_id is None:
            raise CommandError('No such user found')
        elif user_by_name is not None and user_by_id is not None:
            if user_by_name == user_by_id:
                user = user_by_id
            else:
                raise CommandError('Two users match: one by id and one by username')
        else:
            user = user_by_name or user_by_id
        user.billing_account.subscribe_to_product(product_name)
        self.stdout.write(
            '\nSuccessfully subscribed User(id=%s, username=%s, email=%s) to %s\n\n' %
            (user.id, user.username, user.email, product_name)
        )

