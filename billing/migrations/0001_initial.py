# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Account'
        db.create_table('billing_account', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('annoying.fields.AutoOneToOneField')(related_name='billing_account', unique=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('billing', ['Account'])

        # Adding model 'ProductType'
        db.create_table('billing_producttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('billing', ['ProductType'])

        # Adding model 'Subscription'
        db.create_table('billing_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('billing_account', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscriptions', to=orm['billing.Account'])),
            ('product_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscriptions', to=orm['billing.ProductType'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('billing', ['Subscription'])

        # Adding model 'SubscriptionApprovalStatus'
        db.create_table('billing_subscriptionapprovalstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=20)),
            ('subscription', self.gf('django.db.models.fields.related.ForeignKey')(related_name='approval_statuses', to=orm['billing.Subscription'])),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('billing', ['SubscriptionApprovalStatus'])

        # Adding model 'AdjustmentType'
        db.create_table('billing_adjustmenttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('billing', ['AdjustmentType'])

        # Adding model 'Adjustment'
        db.create_table('billing_adjustment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('adjustment_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.AdjustmentType'])),
            ('adjustment_value', self.gf('jsonfield.fields.JSONField')()),
            ('subscription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.Subscription'])),
        ))
        db.send_create_signal('billing', ['Adjustment'])


    def backwards(self, orm):
        
        # Deleting model 'Account'
        db.delete_table('billing_account')

        # Deleting model 'ProductType'
        db.delete_table('billing_producttype')

        # Deleting model 'Subscription'
        db.delete_table('billing_subscription')

        # Deleting model 'SubscriptionApprovalStatus'
        db.delete_table('billing_subscriptionapprovalstatus')

        # Deleting model 'AdjustmentType'
        db.delete_table('billing_adjustmenttype')

        # Deleting model 'Adjustment'
        db.delete_table('billing_adjustment')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'billing.account': {
            'Meta': {'object_name': 'Account'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('annoying.fields.AutoOneToOneField', [], {'related_name': "'billing_account'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'billing.adjustment': {
            'Meta': {'object_name': 'Adjustment'},
            'adjustment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.AdjustmentType']"}),
            'adjustment_value': ('jsonfield.fields.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Subscription']"})
        },
        'billing.adjustmenttype': {
            'Meta': {'object_name': 'AdjustmentType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'billing.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'billing.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'billing_account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriptions'", 'to': "orm['billing.Account']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriptions'", 'to': "orm['billing.ProductType']"})
        },
        'billing.subscriptionapprovalstatus': {
            'Meta': {'object_name': 'SubscriptionApprovalStatus'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '20'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'approval_statuses'", 'to': "orm['billing.Subscription']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['billing']
