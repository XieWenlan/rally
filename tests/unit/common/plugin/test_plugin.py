# Copyright 2015: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rally.common.plugin import plugin
from rally import exceptions
from tests.unit import test


class PluginModuleTestCase(test.TestCase):

    def test_deprecated_cls(self):

        @plugin.deprecated("God why?", "0.0.2")
        @plugin.configure(name="deprecated_class_plugin_check")
        class MyPlugin(plugin.Plugin):
            pass

        self.assertEqual({"reason": "God why?", "rally_version": "0.0.2"},
                         MyPlugin.is_deprecated())

    def test_configure_cls(self):

        @plugin.configure(name="get_name_class_plugin")
        class MyPlugin(plugin.Plugin):
            pass

        self.assertEqual("get_name_class_plugin", MyPlugin.get_name())

    def test_configure_two_cls_with_same_names(self):
        name = ".".join(self.id().rsplit(".", 2)[1:])

        @plugin.base()
        class FooBase(plugin.Plugin):
            pass

        @plugin.configure(name=name)
        class MyPlugin(FooBase):
            pass

        try:
            @plugin.configure(name=name)
            class MyPlugin2(FooBase):
                pass

        except exceptions.PluginWithSuchNameExists:
            self.assertEqual([MyPlugin], FooBase.get_all())
        else:
            self.fail("Registration two plugins with same names in one "
                      "namespace should raise an exception.")

    def test_configure_different_bases(self):
        name = "test_configure_different_bases"

        @plugin.base()
        class OneBase(plugin.Plugin):
            pass

        @plugin.base()
        class SecondBase(plugin.Plugin):
            pass

        @plugin.configure(name, platform=name)
        class A(OneBase):
            pass

        @plugin.configure(name, platform=name)
        class B(SecondBase):
            pass

        self.assertEqual(A, OneBase.get(name))
        self.assertEqual(B, SecondBase.get(name))

    def test_get_multiple_chooses(self):
        name = "test_get_multiple_chooses"

        @plugin.base()
        class OneBase(plugin.Plugin):
            pass

        @plugin.base()
        class SecondBase(plugin.Plugin):
            pass

        @plugin.configure(name, platform=name)
        class A(OneBase):
            pass

        @plugin.configure(name, platform=name)
        class B(SecondBase):
            pass

        self.assertRaises(exceptions.MultipleMatchesFound, plugin.Plugin.get,
                          name, name)


@plugin.configure(name="test_base_plugin")
class BasePlugin(plugin.Plugin):
    pass


@plugin.configure(name="test_some_plugin")
class SomePlugin(BasePlugin):
    pass


@plugin.configure(name="test_my_plugin")
class MyPluginInDefault(BasePlugin):
    pass


@plugin.configure(name="test_my_plugin", platform="foo")
class MyPluginInFoo(BasePlugin):
    pass


@plugin.configure(name="test_hidden_plugin", hidden=True)
class HiddenPlugin(BasePlugin):
    pass


@plugin.deprecated("some_reason", "0.1.1")
@plugin.configure(name="test_deprecated_plugin")
class DeprecatedPlugin(BasePlugin):
    pass


class NotInitedPlugin(BasePlugin):
    pass


class PluginTestCase(test.TestCase):

    def test_unregister(self):

        @plugin.configure(name="test_some_temp_plugin")
        class SomeTempPlugin(BasePlugin):
            pass

        SomeTempPlugin.unregister()
        self.assertRaises(exceptions.PluginNotFound,
                          BasePlugin.get, "test_some_temp_plugin")

    def test_get(self):
        self.assertEqual(SomePlugin,
                         BasePlugin.get("test_some_plugin"))

    def test_get_fallback_to_default(self):
        self.assertEqual(SomePlugin,
                         BasePlugin.get("test_some_plugin", platform="bar"))

    def test_get_hidden(self):
        self.assertEqual(HiddenPlugin,
                         BasePlugin.get("test_hidden_plugin",
                                        allow_hidden=True))

    def test_get_hidden_not_found(self):
        self.assertRaises(exceptions.PluginNotFound,
                          BasePlugin.get, "test_hidden_plugin")

    def test_get_not_found(self):
        self.assertRaises(exceptions.PluginNotFound,
                          BasePlugin.get, "non_existing")

    def test_get_multiple_found(self):

        @plugin.configure("test_2_plugins_with_same_name")
        class A(plugin.Plugin):
            pass

        class B(plugin.Plugin):
            pass

        self.assertRaises(exceptions.PluginWithSuchNameExists,
                          plugin.configure("test_2_plugins_with_same_name"), B)

        A.unregister()

    def test_get_multiple_found_hidden(self):

        @plugin.configure("test_2_plugins_with_same_name", hidden=True)
        class A(plugin.Plugin):
            pass

        class B(plugin.Plugin):
            pass

        self.assertRaises(exceptions.PluginWithSuchNameExists,
                          plugin.configure("test_2_plugins_with_same_name"), B)

        A.unregister()

    def test_get_name(self):
        self.assertEqual("test_some_plugin", SomePlugin.get_name())

    def test_get_all(self):
        self.assertEqual(set([SomePlugin, DeprecatedPlugin,
                              MyPluginInDefault, MyPluginInFoo]),
                         set(BasePlugin.get_all()))
        self.assertEqual([], SomePlugin.get_all())

    def test_get_all_by_name(self):
        self.assertEqual(set([MyPluginInDefault, MyPluginInFoo]),
                         set(BasePlugin.get_all(name="test_my_plugin")))

    def test_get_all_hidden(self):
        self.assertEqual(set([SomePlugin, DeprecatedPlugin, HiddenPlugin,
                              MyPluginInDefault, MyPluginInFoo]),
                         set(BasePlugin.get_all(allow_hidden=True)))

    def test_is_deprecated(self):
        self.assertFalse(SomePlugin.is_deprecated())
        self.assertEqual(DeprecatedPlugin.is_deprecated(),
                         {"reason": "some_reason", "rally_version": "0.1.1"})
