# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector_carepoint.unit import mapper

from .common import SetUpCarepointBase


class TestMapper(SetUpCarepointBase):

    def setUp(self):
        super(TestMapper, self).setUp()

    def _new_record(self):
        return {
            'str': '   test test  ',
            'float': '123.456',
            'int': '1',
        }

    def test_trim(self):
        """ It should return a trim modifier """
        modifier = mapper.trim('str')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertEqual(
            rec['str'].strip(), res
        )

    def test_trim_false(self):
        """ It should return False no field in record """
        modifier = mapper.trim('no_exist')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertFalse(res)

    def test_trim_and_titleize(self):
        """ It should return a trim and title modifier """
        modifier = mapper.trim_and_titleize('str')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertEqual(
            rec['str'].strip().title(), res
        )

    def test_trim_and_titleize_false(self):
        """ It should return False no field in record """
        modifier = mapper.trim_and_titleize('no_exist')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertFalse(res)

    def test_to_float(self):
        """ It should return a to float modifier """
        modifier = mapper.to_float('float')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertEqual(
            float(rec['float']), res
        )

    def test_to_float_false(self):
        """ It should return False when no field in record """
        modifier = mapper.to_float('no_exist')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertFalse(res)

    def test_to_int(self):
        """ It should return a to int modifier """
        modifier = mapper.to_int('int')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertEqual(
            int(rec['int']), res
        )

    def test_to_int_false(self):
        """ It should return False when no field in record """
        modifier = mapper.to_int('no_exist')
        rec = self._new_record()
        res = modifier(False, rec, False)
        self.assertFalse(res)
