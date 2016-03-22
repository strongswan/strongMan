from django.test import TestCase
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciSocketException, ViciLoadException


class ViciWrapperTest(TestCase):

        def test_vici_socket(self):
            with self.assertRaises(ViciSocketException):
                self.vici_wrapper = ViciWrapper(socket_path="/")