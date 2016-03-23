from unittest import mock
from django.test import TestCase
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciSocketException, ViciLoadException


class ViciWrapperTest(TestCase):
    def test_vici_socket(self):
        with self.assertRaises(ViciSocketException):
            ViciWrapper(socket_path="/")


class ViciWrapperTestWithMock(TestCase):
    def setUp(self):
        self.vici_mock = mock.Mock(return_value="test")

    def test_vici_socket(self):
        ViciWrapper._connect_socket = self.vici_mock
        vici_wrapper = ViciWrapper()
        self.assertEquals("test", vici_wrapper._connect_socket())
