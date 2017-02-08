# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
import pytz
from datetime import timedelta, datetime

from .common import SetUpCarepointBase

from openerp import fields
from openerp.exceptions import ValidationError

from openerp.addons.connector_carepoint.models.carepoint_backend import (
    IMPORT_DELTA_BUFFER
)


model = 'openerp.addons.connector_carepoint.models.carepoint_backend'


class TestCarepointBackend(SetUpCarepointBase):

    def setUp(self):
        super(TestCarepointBackend, self).setUp()
        self.Model = self.env['carepoint.backend']

    def test_check_default_for_company(self):
        """ It should not allow two defaults for the same company """
        with self.assertRaises(ValidationError):
            self.backend.copy({
                'sale_prefix': 'TEST',
                'rx_prefix': 'RXTEST',
            })

    def test_select_versions(self):
        """ It should return proper versions """
        self.assertEqual(
            [('2.99', '2.99+')],
            self.Model.select_versions(),
        )

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_synchronize_metadata_imports_pharmacy(self, session, batch):
        """ It should run import_batch for pharmacy on backend """
        self.backend.synchronize_metadata()
        batch.assert_called_once_with(
            session(), 'carepoint.carepoint.store', self.backend.id,
        )

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_all_checks_stucture(self, session, batch):
        """ It should check internal structure on all backends """
        self.backend._import_all('model')
        batch.assert_called_once_with(
            session(), 'carepoint.carepoint.store', self.backend.id,
        )

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_all_calls_import(self, session, batch):
        """ It should call delayed batch import for model """
        expect = 'model'
        self.backend._import_all(expect)
        batch.delay.assert_called_once_with(
            session(), expect, self.backend.id,
        )

    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_from_date_checks_stucture(self, session, batch):
        """ It should check internal structure on all backends """
        self.backend._import_from_date('model', 'import_patients_from_date')
        batch.assert_called_once_with(
            session(), 'carepoint.carepoint.store', self.backend.id,
        )

    @mock.patch('%s.datetime' % model)
    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_from_date_calls_import(self, session, batch, dt_mk):
        """ It should call delayed batch import for model """
        expect = 'model', 'import_patients_from_date', 'chg'
        dt_mk.utcnow.return_value = datetime.utcnow()
        expect_date = dt_mk.utcnow() - timedelta(days=5)
        self.backend.import_patients_from_date = expect_date
        expect_date = self.backend.import_patients_from_date
        self.backend._import_from_date(*expect)
        utc_now = pytz.timezone('UTC').localize(dt_mk.utcnow()).astimezone(
            pytz.timezone(self.backend.server_tz)
        )
        batch.delay.assert_called_once_with(
            session(), expect[0], self.backend.id,
            filters={
                expect[2]: {
                    '>=': fields.Datetime.from_string(
                        expect_date,
                    ),
                    '<=': utc_now.replace(tzinfo=None),
                },
            }
        )

    @mock.patch('%s.datetime' % model)
    @mock.patch('%s.import_batch' % model)
    @mock.patch('%s.ConnectorSession' % model)
    def test_import_from_date_writes_new_date(self, session, batch, dt_mk):
        """ It should call delayed batch import for model """
        dt_mk.utcnow.return_value = datetime.utcnow()
        expect_date = dt_mk.utcnow() - timedelta(days=5)
        self.backend.import_patients_from_date = expect_date
        self.backend._import_from_date(
            'model', 'import_patients_from_date', 'chg'
        )
        utc_now = pytz.timezone('UTC').localize(dt_mk.utcnow())
        local_now = utc_now.astimezone(
            pytz.timezone(self.backend.default_tz)
        )
        expect = local_now - timedelta(seconds=IMPORT_DELTA_BUFFER)
        self.assertEqual(
            fields.Datetime.to_string(expect),
            self.backend.import_patients_from_date,
        )

    def test_cron_import_medical_prescription_search(self):
        """ It should search for all backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_prescription()
            mk.assert_called_once_with([])

    def test_cron_import_medical_prescription_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_prescription()
            mk().import_medical_prescription.assert_called_once_with()

    def test_cron_import_medical_patient_search(self):
        """ It should search for all backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_patient()
            mk.assert_called_once_with([])

    def test_cron_import_medical_patient_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_patient()
            mk().import_medical_patient.assert_called_once_with()

    def test_cron_import_medical_physician_search(self):
        """ It should search for all backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_physician()
            mk.assert_called_once_with([])

    def test_cron_import_medical_physician_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_medical_physician()
            mk().import_medical_physician.assert_called_once_with()

    def test_cron_import_address_search(self):
        """ It should search for all backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_address()
            mk.assert_called_once_with([])

    def test_cron_import_address_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_address()
            mk().import_address.assert_called_once_with()

    def test_cron_import_sale_order_search(self):
        """ It should search for all backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_sale_order()
            mk.assert_called_once_with([])

    def test_cron_import_sale_order_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_sale_order()
            mk().import_sale_order.assert_called_once_with()

    def test_cron_import_phone_import(self):
        """ It should call import on found backends """
        with mock.patch.object(self.backend, 'search') as mk:
            self.backend.cron_import_phone()
            mk().import_phone.assert_called_once_with()

    def test_import_carepoint_item(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_carepoint_item()
            mk.assert_called_once_with(
                'carepoint.carepoint.item',
                'import_items_from_date',
            )

    def test_import_medical_patient(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_medical_patient()
            mk.assert_called_once_with(
                'carepoint.medical.patient',
                'import_patients_from_date',
            )

    def test_import_medical_physician(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_medical_physician()
            mk.assert_called_once_with(
                'carepoint.medical.physician',
                'import_physicians_from_date',
            )

    def test_import_addresses(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_address()
            mk.assert_called_once_with(
                'carepoint.carepoint.address',
                'import_addresses_from_date',
            )

    def test_import_medical_prescription(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_medical_prescription()
            mk.assert_called_once_with(
                'carepoint.rx.ord.ln',
                'import_prescriptions_from_date',
            )

    def test_import_sale_order(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_sale_order()
            mk.assert_called_once_with(
                'carepoint.sale.order.line',
                'import_sales_from_date',
            )

    def test_import_stock_picking(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_stock_picking()
            mk.assert_called_once_with(
                'carepoint.stock.picking',
                'import_pickings_from_date',
            )

    def test_import_account_invoice(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_account_invoice()
            mk.assert_called_once_with(
                'carepoint.account.invoice.line',
                'import_invoices_from_date',
                'primary_pay_date',
            )

    def test_import_phone(self):
        """ It should import proper model on date field """
        with mock.patch.object(self.backend, '_import_from_date') as mk:
            self.backend.import_phone()
            mk.assert_called_once_with(
                'carepoint.carepoint.phone',
                'import_phones_from_date',
            )

    def test_import_fdb(self):
        """ It should import all of the required FDB models """
        with mock.patch.object(self.backend, '_import_all') as mk:
            self.backend.import_fdb()
            mk.assert_has_calls([
                mock.call('carepoint.fdb.route'),
                mock.call('carepoint.fdb.form'),
                mock.call('carepoint.fdb.unit'),
            ])
