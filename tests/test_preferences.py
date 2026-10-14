"""Exercise preference transactions with a fake store, without a HA runtime."""
import ast
import asyncio
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

source = Path(__file__).parents[1] / 'custom_components/dsj_dashboard/__init__.py'
tree = ast.parse(source.read_text())
manager_node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'DSJManager')

class FakeStore:
    def __init__(self, *args):
        self.saved = None
        self.fail = False
    async def async_save(self, data):
        await asyncio.sleep(0)
        if self.fail:
            raise OSError('disk unavailable')
        self.saved = deepcopy(data)

namespace = {'asyncio': asyncio, 'deepcopy': deepcopy, 'Store': FakeStore,
             'DOMAIN': 'dsj_dashboard', 'callback': lambda f: f,
             'DSJLovelace': lambda manager: object(),
             'er': SimpleNamespace(async_get=lambda hass: SimpleNamespace(async_get=lambda eid: None))}
exec(compile(ast.Module(body=[manager_node], type_ignores=[]), str(source), 'exec'), namespace)

class PreferenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        hass = SimpleNamespace(states=SimpleNamespace(get=lambda eid: object() if eid in {'light.a','light.b','light.new'} else None))
        self.manager = namespace['DSJManager'](hass, None, None)
        self.refreshes = 0
        def schedule():
            self.refreshes += 1
        self.manager.schedule = schedule

    async def test_hide_is_saved_and_can_be_reversed(self):
        await self.manager.change('light.a', 'hide', True)
        self.assertEqual(self.manager.store.saved['hidden'], ['light.a'])
        await self.manager.change('light.a', 'hide', False)
        self.assertEqual(self.manager.store.saved['hidden'], [])
        self.assertEqual(self.refreshes, 2)

    async def test_concurrent_changes_do_not_overwrite_each_other(self):
        await asyncio.gather(self.manager.change('light.a', 'hide', True), self.manager.change('light.b', 'favorite', True))
        self.assertEqual(self.manager.store.saved, {'hidden':['light.a'], 'favorites':['light.b']})

    async def test_failed_save_does_not_change_live_settings(self):
        self.manager.store.fail = True
        with self.assertRaises(OSError):
            await self.manager.change('light.a', 'hide', True)
        self.assertEqual(self.manager.preferences['hidden'], [])
        self.assertEqual(self.refreshes, 0)

    async def test_rename_preserves_hidden_and_favorite(self):
        self.manager.preferences = {'hidden':['light.a'], 'favorites':['light.a','light.new']}
        await self.manager.rename('light.a','light.new')
        self.assertEqual(self.manager.preferences, {'hidden':['light.new'], 'favorites':['light.new']})

    async def test_unknown_entity_is_rejected(self):
        with self.assertRaises(ValueError):
            await self.manager.change('light.missing', 'hide', True)
        self.assertIsNone(self.manager.store.saved)

if __name__ == '__main__':
    unittest.main()
