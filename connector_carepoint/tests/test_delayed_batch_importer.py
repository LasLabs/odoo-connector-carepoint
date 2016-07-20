# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.unit import import_synchronizer

from .common import SetUpCarepointBase

model = 'openerp.addons.connector_carepoint.unit.import_synchronizer'


class TestDelayedBatchImporter(SetUpCarepointBase):

    def setUp(self):
        super(TestDelayedBatchImporter, self).setUp()
        self.Importer = import_synchronizer.DelayedBatchImporter
        self.model = 'carepoint.medical.pharmacy'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    def _new_importer(self, carepoint_id=None, carepoint_record=None):
        importer = self.Importer(self.mock_env)
        if carepoint_id is not None:
            importer.carepoint_id = carepoint_id
        if carepoint_record is not None:
            importer.carepoint_record = carepoint_record
        return importer

    def test_import_record(self):
        """ It should call import_record w/ proper args """
        importer = self._new_importer()
        expect = 'expect'
        kwargs = {'test1': 1234, 'test2': 5678}
        with mock.patch('%s.import_record' % model) as mk:
            with mock.patch('%s.int_or_str' % model) as int_or_str:
                importer._import_record(expect, **kwargs)
                mk.delay.assert_called_once_with(
                    importer.session,
                    importer.model._name,
                    importer.backend_record.id,
                    int_or_str(expect),
                    **kwargs
                )
