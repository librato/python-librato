# coding=utf-8
import unittest
from librato import sanitize_no_op, sanitize_metric_name


class TestSanitization(unittest.TestCase):
    def test_sanitize_no_op(self):
        for name in ['323***', 'name1', 'name2']:
            self.assertEquals(name, sanitize_no_op(name))

    def test_sanitize_metric_name(self):
        valid_chars = 'abcdefghijklmnopqrstuvwxyz.:-_'
        for name, expected in [
            (valid_chars, valid_chars),
            (valid_chars.upper(), valid_chars.upper()),
            ('a'*500, 'a'*255),
            ('   \t\nbat$$$*[]()m#@%^&=`~💩an', 'batman')  # throw in a unicode char
        ]:
            self.assertEquals(sanitize_metric_name(name), expected)