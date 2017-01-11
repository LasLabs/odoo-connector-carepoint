# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import (
    medical_prescription_order_line
)

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.%s' % (
    'medical_prescription_order_line'
)


class EndTestException(Exception):
    pass


class MedicalPrescriptionOrderLineTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPrescriptionOrderLineTestBase, self).setUp()
        self.model = 'carepoint.rx.ord.ln'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'refills_orig': 1,
            'days_supply': 2,
            'ndc': ' 13234324 ',
            'daw_yn': False,
            'pat_id': 3,
            'gcn_seqno': 4,
            'md_id': 5,
            'rx_id': 6,
            'script_no': 7,
            'sig_code': ' sig code ',
            'sig_text_english': ' sig text english ',
        }


class TestMedicalPrescriptionOrderLineImportMapper(
    MedicalPrescriptionOrderLineTestBase
):

    def setUp(self):
        super(TestMedicalPrescriptionOrderLineImportMapper, self).setUp()
        self.Unit = medical_prescription_order_line.\
            MedicalPrescriptionOrderLineImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['rx_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_name(self):
        """ It should return properly formatted name """
        expect = '{prefix}{name}'.format(
            prefix=self.unit.backend_record.rx_prefix,
            name=self.record['script_no'],
        )
        expect = {'name': expect}
        res = self.unit.name(self.record)
        self.assertDictEqual(expect, res)

    def test_duration(self):
        """ It should perform and return proper duration cals """
        expect = (self.record['refills_orig'] + 1)
        expect = self.record['days_supply'] * expect
        expect = {'duration': expect}
        res = self.unit.duration(self.record)
        self.assertDictEqual(expect, res)

    def test_medicament_and_meta_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.medicament_and_meta(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.ndc'
            )

    def test_medicament_and_meta_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.medicament_and_meta(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['ndc'], browse=True,
            )

    def test_medicament_and_meta_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            ndc_id = self.unit.binder_for().to_odoo()
            expect = {
                'medicament_id': ndc_id.medicament_id.id,
                'dose_uom_id': ndc_id.medicament_id.uom_id.id,
                'dispense_uom_id': ndc_id.medicament_id.uom_id.id,
            }
            res = self.unit.medicament_and_meta(self.record)
            self.assertDictEqual(expect, res)

    def test_is_substitutable(self):
        """ It should return properly formatted name """
        expect = {'is_substitutable': True}
        res = self.unit.is_substitutable(self.record)
        self.assertDictEqual(expect, res)

    def test_patient_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.patient_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.patient'
            )

    def test_patient_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.patient_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['pat_id']
            )

    def test_patient_id_return(self):
        """ It should return the proper values dict """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.patient_id(self.record)
            expect = {'patient_id': self.unit.binder_for().to_odoo()}
            self.assertDictEqual(expect, res)

    def test_ndc_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.ndc_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.ndc'
            )

    def test_ndc_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.ndc_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['ndc'].strip()
            )

    def test_ndc_id_return(self):
        """ It should return the proper values dict """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.ndc_id(self.record)
            expect = {'ndc_id': self.unit.binder_for().to_odoo()}
            self.assertDictEqual(expect, res)

    def test_gcn_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.gcn_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.gcn'
            )

    def test_gcn_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.gcn_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['gcn_seqno']
            )

    def test_medication_dosage_id_search(self):
        """ It should perform proper search for dosage """
        with mock.patch.object(self.unit.session, 'env') as env:
            search = env['medical.medication.dosage'].search
            search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.medication_dosage_id(self.record)
            search.assert_called_once_with(
                [
                    '|',
                    ('name', '=', self.record['sig_text_english'].strip()),
                    ('code', '=', self.record['sig_code'].strip()),
                ],
                limit=1,
            )

    def test_medication_dosage_id_create(self):
        """ It should create dosage if not already existing """
        with mock.patch.object(self.unit.session, 'env') as env:
            search = env['medical.medication.dosage'].search
            search.return_value = []
            self.unit.medication_dosage_id(self.record)
            env['medical.medication.dosage'].create.assert_called_once_with({
                'name': self.record['sig_text_english'].strip(),
                'code': self.record['sig_code'].strip(),
            })

    def test_medication_dosage_id_return_search(self):
        """ It should return result of search if existing """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit.session, 'env') as env:
            search = env['medical.medication.dosage'].search
            search.return_value = [expect]
            res = self.unit.medication_dosage_id(self.record)
            expect = {'medication_dosage_id': expect.id}
            self.assertDictEqual(expect, res)

    def test_medication_dosage_id_return_create(self):
        """ It should return result of create if not existing """
        with mock.patch.object(self.unit.session, 'env') as env:
            search = env['medical.medication.dosage'].search
            search.return_value = []
            res = self.unit.medication_dosage_id(self.record)
            expect = env['medical.medication.dosage'].create()[0]
            expect = {'medication_dosage_id': expect.id}
            self.assertDictEqual(expect, res)

    def test_duration_uom_id_days(self):
        """ It should find UOM for days """
        with mock.patch.object(self.unit.session, 'env') as env:
            search = env['product.uom'].search
            search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.duration_uom_id(self.record)
            search.assert_called_once_with([('name', '=', 'DAYS')], limit=1)

    def test_duration_uom_id_return(self):
        """ It should return proper values dict """
        with mock.patch.object(self.unit.session, 'env') as env:
            res = self.unit.duration_uom_id(self.record)
            expect = {
                'duration_uom_id': env['product.uom'].search().id
            }
            self.assertEqual(expect, res)

    def test_gcn_id_return(self):
        """ It should return the proper values dict """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.gcn_id(self.record)
            expect = {'gcn_id': self.unit.binder_for().to_odoo()}
            self.assertDictEqual(expect, res)

    def test_physician_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.physician_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.physician'
            )

    def test_physician_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.physician_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['md_id']
            )

    def test_physician_id_return(self):
        """ It should return the proper values dict """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.physician_id(self.record)
            expect = {'physician_id': self.unit.binder_for().to_odoo()}
            self.assertDictEqual(expect, res)

    def test_prescription_order_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.prescription_order_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.prescription.order'
            )

    def test_prescription_order_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.prescription_order_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rx_id']
            )

    def test_prescription_order_id_return(self):
        """ It should return the proper values dict """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.prescription_order_id(self.record)
            expect = {
                'prescription_order_id': self.unit.binder_for().to_odoo()
            }
            self.assertDictEqual(expect, res)


class TestMedicalPrescriptionOrderLineImporter(
    MedicalPrescriptionOrderLineTestBase
):

    def setUp(self):
        super(TestMedicalPrescriptionOrderLineImporter, self).setUp()
        self.Unit = medical_prescription_order_line.\
            MedicalPrescriptionOrderLineImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['rx_id'],
                    'carepoint.medical.prescription.order',
                ),
                mock.call(
                    self.record['ndc'],
                    'carepoint.fdb.ndc',
                ),
            ])
