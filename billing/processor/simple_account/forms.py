from django import forms

from billing.processor.simple_account.models import IOUAccount, AccountIOU

class IOUAccountCreationForm(forms.ModelForm):
    def save(self, commit=True):
        iou = super(IOUAccountCreationForm, self).save(commit=False)
        iou_account = IOUAccount(billing_account=self.billing_account)
        iou_account.save()
        iou.iou_account = iou_account
        if commit:
            iou.save()
        return iou
    class Meta:
        model = AccountIOU
        fields = ('has_agreed_to_pay',)

class IOUAccountUpdateForm(forms.ModelForm):
    def save(self, commit=True):
        iou = super(IOUAccountUpdateForm, self).save(commit=False)
        iou_account = self.billing_account.simple_processor_iou_account
        iou.iou_account = iou_account
        if commit:
            iou.save()
        return iou
    class Meta:
        model = AccountIOU
        fields = ('has_agreed_to_pay',)

def get_billing_details_form(billing_account):
    """
    If the billing account already has an IOU account, return the update
    form. If there isn't an account yet, then return the creation form
    """
    try:
        iou_account = billing_account.simple_processor_iou_account
        return IOUAccountUpdateForm
    except IOUAccount.DoesNotExist:
        return IOUAccountCreationForm
