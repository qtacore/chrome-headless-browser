# -*- coding: utf-8 -*-

'''单元测试
'''

import unittest
import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(test_dir))


def main():
    runner = unittest.TextTestRunner(verbosity=10 + sys.argv.count('-v'))
    suite = unittest.TestLoader().discover(test_dir, pattern='test_*.py')
    raise SystemExit(not runner.run(suite).wasSuccessful())


if __name__ == '__main__':
    main()
