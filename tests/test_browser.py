# -*- coding: utf-8 -*-

import sys
import subprocess
import unittest
try:
    from unittest import mock
except:
    import mock

import chrome_master
from chrome_headless.browser import ChromeHeadlessBrowser
from qt4w.webcontrols import WebPage

from tests.util import MockDebugger


def generic_func(*args, **kwargs):
    pass


subprocess.Popen = mock.Mock(side_effect=generic_func)
chrome_master.ChromeMaster.find_page = mock.Mock(return_value=MockDebugger())
ChromeHeadlessBrowser.check_server = mock.Mock(return_value=True)


class ChromeHeadlessBrowserTest(unittest.TestCase):
    '''ChromeHeadlessBrowser单元测试
    '''

    def test_open_url(self):
        browser = ChromeHeadlessBrowser()
        webpage = browser.open_url('about:blank')
        self.assertIsInstance(webpage, WebPage)
