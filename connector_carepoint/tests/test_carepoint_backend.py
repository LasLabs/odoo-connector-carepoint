# -*- coding: utf-8 -*-
# © 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from .common import SetUpCarepointBase

from openerp.exceptions import ValidationError


model = 'openerp.addons.connector_carepoint.models.carepoint_backend'


class TestCarepointBackend(SetUpCarepointBase):

    def setUp(self):
        super(TestCarepointBackend, self).setUp()
        self.Model = self.env['connector.carepoint']

    def test_check_default_for_company(self):
        """ It should not allow two defaults for the same company """
        with self.assertRaises(ValidationError):
            self.backend.copy()

    def test_select_versions(self):
        """ It should return proper versions """
        self.assertEqual(
            [('2.99', '2.99+')],
            self.Model.select_versions(),
        )

    @mock.patch('%s.ConnectorSession' % model)
    def test_get_session_creates_session(self, mk):
        """ It should create proper ConnectorSession """
        self.Model.__get_session()
        mk.assert_called_once_with(
            self.Model.env.cr,
            self.Model.env.uid,
            context=self.Model.env.context,
        )

    @mock.patch('%s.ConnectorSession' % model)
    def test_get_session_returns_session(self, mk):
        """ It should return ConnectorSession """
        res = self.Model.__get_session()
        self.AssertEqual(
            mk(), res,
        )

    def test_check_carepoint_structure(self):
        """ It should iterate backends and run synchronize_metadata """
        with mock.patch.object(self.backend[0], 'synchronize_metadata') as mk:
            self.backend.check_carepoint_structure()
            mk.assert_called_once_with()

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_synchronize_metadata_imports_pharmacy(self, session, batch):
        """ It should run import_batch for pharmacy on backend """
        self.backend.synchronize_metadata()
        batch.assert_called_once_with(
            session(), 'carepoint.medical.pharmacy', self.backend.id,
        )

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_all(self, session, batch):
        """ It should currently fail """
        self.assertTrue(False)
