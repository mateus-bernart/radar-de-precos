import copy
import datetime as dt
import unittest
from unittest.mock import patch
import update_prices as app

ACCOUNT={'account_status':'Active','plan_id':'free','plan_name':'Free Plan','plan_monthly_price':0,
 'searches_per_month':250,'this_month_usage':0,'plan_searches_left':250,'total_searches_left':250,'plan_renewal_date':'2026-12-01'}
NOW=dt.datetime(2026,11,21,13,tzinfo=dt.timezone.utc)
PRODUCT={'id':'test','model':'Q27G4F','query':'AOC Q27G4F'}
class Safety(unittest.TestCase):
 def test_free(self):
  self.assertEqual(app.quota(ACCOUNT)['safe_remaining'],190)
 def test_missing_or_paid_fields(self):
  for key in ACCOUNT:
   a=ACCOUNT.copy();a.pop(key)
   with self.subTest(missing=key),self.assertRaises(app.SafeStop):app.quota(a)
  for changes in ({'plan_monthly_price':25},{'plan_id':'starter'},{'plan_name':'Starter'},{'plan_monthly_price':None},{'searches_per_month':1000},{'this_month_usage':'0'},{'plan_searches_left':251},{'plan_renewal_date':None}):
   with self.subTest(changes=changes),self.assertRaises(app.SafeStop):app.quota({**ACCOUNT,**changes})
 def test_reserve(self):
  a={**ACCOUNT,'this_month_usage':190,'plan_searches_left':60,'total_searches_left':60}
  with patch.object(app,'get_json',return_value=a) as fetch:
   self.assertEqual(app.collect({},[PRODUCT],'secret',NOW),0);self.assertEqual(fetch.call_count,1)
 def test_model_boundaries(self):
  self.assertTrue(app.matches(PRODUCT,'Monitor AOC Q27G4F IPS'))
  for title in ('AOC CQ27G4F','AOC Q27G4FA','AOC Q27G4'):
   self.assertFalse(app.matches(PRODUCT,title))
  self.assertFalse(app.matches({'model':'24G4/P'},'AOC 24G4E'))
 def test_samsung_size(self):
  p={'model':'S30GD','size_required':True}
  self.assertFalse(app.matches(p,'Samsung S30GD 27 polegadas'))
  self.assertTrue(app.matches(p,'Samsung S30GD 24 polegadas'))
 def test_interval_and_special_days(self):
  data={'product_checks':{'test':NOW.isoformat()}}
  self.assertFalse(app.due(PRODUCT,data,NOW+dt.timedelta(hours=47)))
  self.assertTrue(app.due(PRODUCT,data,NOW+dt.timedelta(hours=48)))
  special=dt.datetime(2026,11,27,13,tzinfo=dt.timezone.utc)
  self.assertTrue(app.due(PRODUCT,{'product_checks':{'test':(special-dt.timedelta(hours=24)).isoformat()}},special))
 def test_account_failure_stops_search(self):
  with patch.object(app,'get_json',side_effect=app.SafeStop('Falha')) as fetch:
   with self.assertRaises(app.SafeStop):app.collect({},[PRODUCT],'secret',NOW)
   self.assertEqual(fetch.call_count,1)
 def test_no_search_on_push_policy(self):
  from pathlib import Path
  self.assertIn("if: github.event_name != 'push'",Path('.github/workflows/prices.yml').read_text())
 def test_errors_not_success(self):
  with patch.object(app,'get_json',side_effect=[ACCOUNT,{'error':'bad'}]):
   data={}
   with self.assertRaises(app.SafeStop):app.collect(data,[PRODUCT],'secret',NOW)
   self.assertEqual(data['prices'],[]);self.assertNotIn('test',data['product_checks'])
 def test_local_counter_stops_stale_account(self):
  a={**ACCOUNT,'this_month_usage':189,'plan_searches_left':61,'total_searches_left':61}
  calls=[]
  def fetch(endpoint,params):
   calls.append(endpoint)
   return copy.deepcopy(a) if endpoint=='account.json' else {'search_metadata':{'status':'Success'},'shopping_results':[]}
  with patch.object(app,'get_json',side_effect=fetch):
   self.assertEqual(app.collect({},[PRODUCT,{**PRODUCT,'id':'other'}],'secret',NOW),1)
  self.assertEqual(calls.count('search.json'),1)
 def test_records_and_deduplication(self):
  item={'title':'AOC Q27G4F IPS','price':'R$ 899,00','extracted_price':899,'source':'Loja','link':'https://example.com/monitor'}
  response={'search_metadata':{'status':'Success'},'shopping_results':[item,item,{**item,'title':'CQ27G4F'},{**item,'extracted_price':float('nan')}]}
  with patch.object(app,'get_json',side_effect=[ACCOUNT,response,ACCOUNT]):
   data={'prices':[{'id':'legacy','price':100}]};app.collect(data,[PRODUCT],'secret',NOW)
  self.assertEqual(len(data['prices']),2)
  row=data['prices'][1];self.assertIsNone(row['shipping']);self.assertFalse(row['shippingKnown']);self.assertEqual(row['date'],'2026-11-21')
 def test_partial_history_survives_second_account_failure(self):
  response={'search_metadata':{'status':'Success'},'shopping_results':[{'title':'Q27G4F','price':'R$ 900,00','extracted_price':900}]}
  data={}
  with patch.object(app,'get_json',side_effect=[ACCOUNT,response,app.SafeStop('Falha')]):
   with self.assertRaises(app.SafeStop):app.collect(data,[PRODUCT,{**PRODUCT,'id':'other'}],'secret',NOW)
  self.assertEqual(len(data['prices']),1)
 def test_review_flags(self):
  self.assertTrue(app.review_reason({'refresh_hz':144},'Monitor 100Hz','LG Electronics'))
  self.assertTrue(app.review_reason({},'Monitor','PC House BD'))
  self.assertFalse(app.review_reason({'refresh_hz':144},'Monitor 144Hz','LG Electronics do Brasil'))
 def test_catalog_limit(self):
  with self.assertRaises(app.SafeStop):app.collect({},[{**PRODUCT,'id':str(i)} for i in range(12)],'secret',NOW)
if __name__=='__main__':unittest.main()
