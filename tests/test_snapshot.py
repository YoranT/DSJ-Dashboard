"""Verify current device-registry iteration, not its deprecated mapping API."""
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
from test_preferences import namespace

class DeviceEntries:
    def __iter__(self):
        return iter([NS(id='device1',area_id='living')])
    def values(self):
        raise AssertionError('Deprecated device mapping API used')

class SnapshotTests(unittest.TestCase):
    def test_snapshot_uses_device_entry_iteration(self):
        state = NS(entity_id='light.sofa',attributes={'friendly_name':'Banklamp'})
        record = NS(name=None,original_name='Bank',area_id=None,device_id='device1',platform='demo',labels=set(),hidden_by=None,disabled_by=None,entity_category=None,device_class=None,original_device_class=None)
        registry = NS(entities={'light.sofa':record},async_get=lambda eid: record)
        hass = NS(states=NS(async_all=lambda:[state]))
        fake_registries = {
            'ar':NS(async_get=lambda hass: NS(async_list_areas=lambda:[NS(id='living',name='Woonkamer',floor_id=None,icon=None,temperature_entity_id=None,humidity_entity_id=None)])),
            'fr':NS(async_get=lambda hass: NS(async_list_floors=lambda:[])),
            'dr':NS(async_get=lambda hass: NS(devices=DeviceEntries())),
            'er':NS(async_get=lambda hass: registry),
        }
        with patch.dict(namespace,fake_registries):
            manager = namespace['DSJManager'](hass,None,None)
            areas,floors,entities,devices = manager.snapshot()
        self.assertEqual(devices,{'device1':{'area_id':'living'}})
        self.assertEqual(entities[0]['name'],'Banklamp')
        self.assertEqual(areas[0]['area_id'],'living')
