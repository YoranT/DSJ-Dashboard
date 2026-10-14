"""Resource registration tests without a running Home Assistant instance."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('resources', Path(__file__).parents[1] / 'custom_components/dsj_dashboard/resource_registration.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class YAMLResources:
    def __init__(self):
        self.data = [{'id':'other','type':'module','url':'/local/other.js'}]
        self.loaded = False
    async def async_get_info(self):
        self.loaded = True
    def async_items(self):
        assert self.loaded
        return self.data

class StorageResources(YAMLResources):
    async def async_create_item(self, data):
        self.data.append({'id':'dsj','type':data['res_type'],'url':data['url']})
    async def async_update_item(self, item_id, data):
        next(item for item in self.data if item['id']==item_id).update(type=data['res_type'],url=data['url'])

class ResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_storage_registration_is_idempotent(self):
        resources = StorageResources()
        for _ in range(2):
            await r.ensure_lovelace_resource(resources,'/dsj_dashboard/dsj-dashboard.js?v=0.1.1')
        self.assertEqual(len(resources.data),2)
        self.assertEqual(resources.data[0]['url'],'/local/other.js')
        self.assertEqual(resources.data[1]['type'],'module')

    async def test_old_storage_urls_updated_without_duplicates(self):
        resources = StorageResources()
        resources.data.extend([{'id':'old','url':'/dsj_dashboard/dsj-dashboard.js?v=0.1.0','type':'module'},{'id':'manual','url':'/dsj_dashboard/dsj-dashboard.js','type':'js'}])
        await r.ensure_lovelace_resource(resources,'/dsj_dashboard/dsj-dashboard.js?v=0.1.1')
        self.assertEqual(len(resources.data),3)
        self.assertTrue(all(i['url'].endswith('v=0.1.1') and i['type']=='module' for i in resources.data[1:]))

    async def test_yaml_resources_supported_in_memory(self):
        resources = YAMLResources()
        for _ in range(2):
            await r.ensure_lovelace_resource(resources,'/dsj_dashboard/dsj-dashboard.js?v=0.1.1')
        self.assertEqual(len(resources.data),2)
        self.assertEqual(resources.data[1]['url'],'/dsj_dashboard/dsj-dashboard.js?v=0.1.1')
