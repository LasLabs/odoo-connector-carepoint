# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp import fields

from openerp.addons.connector.exception import IDMissingInBackend

from openerp.addons.connector_carepoint.unit import export_synchronizer

from .common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.unit.export_synchronizer'


class EndTestException(Exception):
    pass


class TestBaseExporter(SetUpCarepointBase):

    def setUp(self):
        super(TestBaseExporter, self).setUp()
        self.model = 'carepoint.medical.pharmacy'
        self.carepoint_id = 'carepoint_id'
        self.binding_id = 1234
        self.Exporter = export_synchronizer.CarepointBaseExporter

    def _new_exporter(self, carepoint_id=None, binding_record=None,
                      binding_id=None,
                      ):
        exporter = self.Exporter(self.get_carepoint_helper(
            self.model
        ))
        exporter.carepoint_id = carepoint_id
        exporter.binding_record = binding_record
        exporter.binding_id = binding_id
        return exporter

    def _new_record(self, sync_date=False):
        return self.env[self.model].create({
            'name': 'Test',
            'sync_date': sync_date,
        })

    def test_exporter_init_binding_id(self):
        """ It should init binding_id as None """
        exporter = self._new_exporter()
        self.assertEqual(None, exporter.binding_id)

    def test_exporter_init_carepoint_id(self):
        """ It should init carepoint_id as None """
        exporter = self._new_exporter()
        self.assertEqual(None, exporter.carepoint_id)

    def test_delay_import_assets_carepoint_id(self):
        """ It should not allow a false carepoint_id """
        exporter = self._new_exporter()
        with self.assertRaises(AssertionError):
            exporter._delay_import()

    @mock.patch('%s.import_record' % model)
    def test_delay_import_delays_import(self, mk):
        """ It should call delayed import w/ proper args """
        exporter = self._new_exporter(self.carepoint_id)
        exporter._delay_import()
        mk.delay.assert_called_once_with(
            exporter.session,
            exporter.model._name,
            exporter.backend_record.id,
            exporter.carepoint_id,
            force=True,
        )

    def test_should_import_asserts_binding(self):
        """ It should throw AssertionError on no binding_record """
        exporter = self._new_exporter()
        with self.assertRaises(AssertionError):
            exporter._should_import()

    def test_should_import_false_carepoint_id(self):
        """ It should return False when no carepoint_id """
        exporter = self._new_exporter(
            binding_record=self._new_record()
        )
        res = exporter._should_import()
        self.assertFalse(res)

    def test_should_import_no_previous_sync(self):
        """ It should return True when there is not a previous sync """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record(),
        )
        res = exporter._should_import()
        self.assertTrue(res)

    def test_should_import_gets_record(self):
        """ It should get record from backend """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with self.mock_adapter(exporter) as adapter:
            exporter._should_import()
            adapter.read.assert_called_once_with(
                self.carepoint_id, attributes=['chg_date']
            )

    def test_should_import_no_chg_date(self):
        """ It should return False when no chg_date col """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with self.mock_adapter(exporter) as adapter:
            adapter.read.return_value = {
                'chg_date': False
            }
            res = exporter._should_import()
            self.assertFalse(res)

    def test_should_import_not_changed(self):
        """ It should return False if the record is not changed """
        expect = '2016-06-12 00:00:00'
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record(expect),
        )
        with self.mock_adapter(exporter) as adapter:
            adapter.read.return_value = {
                'chg_date': fields.Datetime.from_string(
                    expect
                )
            }
            res = exporter._should_import()
            self.assertFalse(res)

    def test_should_import_is_changed(self):
        """ It should return True if the record is changed """
        expect = '2016-06-12 00:00:00'
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record(expect),
        )
        with self.mock_adapter(exporter) as adapter:
            adapter.read.return_value = {
                'chg_date': fields.Datetime.from_string(
                    expect.replace('6', '7')
                )
            }
            res = exporter._should_import()
            self.assertTrue(res)

    def test_get_odoo_data_browse(self):
        """ It should browse model for binding """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
            binding_id=self.binding_id,
        )
        with mock.patch.object(exporter.connector_env, 'model') as mk:
            exporter._get_odoo_data()
            mk.browse.assert_called_once_with(self.binding_id)

    def test_get_odoo_data_return(self):
        """ It should return browse record """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
            binding_id=self.binding_id,
        )
        with mock.patch.object(exporter.connector_env, 'model') as mk:
            res = exporter._get_odoo_data()
            self.assertEqual(mk.browse(), res)

    def test_run_sets_binding_id(self):
        """ It should set binding_id on instance """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_get_odoo_data') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                exporter.run(self.binding_id)
            self.assertEqual(
                self.binding_id, exporter.binding_id,
            )

    def test_run_gets_backend(self):
        """ It should get the backend for binding """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter.binder, 'to_backend') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                exporter.run(self.binding_id)
            mk.assert_called_once_with(self.binding_id)

    def test_run_should_import(self):
        """ It should see if the record needs to be imported """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                exporter.run(self.binding_id)

    def test_run_should_import_missing_carepoint_id(self):
        """ It should set carepoint_id to None if missing """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as mk:
            with mock.patch.object(exporter, '_run') as run:
                mk.side_effect = IDMissingInBackend
                run.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    exporter.run(self.binding_id)
                self.assertEqual(
                    None, exporter.carepoint_id,
                )

    def test_run_should_import_true(self):
        """ It should call delay import if should_import """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as should:
            should.return_value = True
            with mock.patch.object(exporter, '_delay_import') as mk:
                mk.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    exporter.run(self.binding_id)

    def test_run_calls_private_run(self):
        """ It should call private run interface with args """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        expect_list = [1, 2, 3]
        expect_dict = {'1': 'test', '2': 'derp'}
        with mock.patch.object(exporter, '_should_import') as mk:
            mk.return_value = False
            with mock.patch.object(exporter, '_run') as mk:
                mk.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    exporter.run(self.binding_id, *expect_list, **expect_dict)
                mk.assert_called_once_with(*expect_list, **expect_dict)

    def test_run_calls_bind(self):
        """ It should call bind with proper args """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as mk:
            mk.return_value = False
            with mock.patch.object(exporter, '_run'):
                with mock.patch.object(exporter, '_binder') as binder:
                    binder.bind.side_effect = EndTestException
                    with self.assertRaises(EndTestException):
                        exporter.run(self.binding_id)
                    binder.bind.assert_called_once_with(
                        binder.to_backend(), self.binding_id,
                    )

    def test_run_commits_session(self):
        """ It should commit session for export isolation """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as mk:
            mk.return_value = False
            with mock.patch.object(exporter, '_run'):
                with mock.patch.object(exporter.binder, 'bind'):
                    with mock.patch.object(exporter, 'session') as session:
                        session.commit.side_effect = EndTestException
                        with self.assertRaises(EndTestException):
                            exporter.run(self.binding_id)

    def test_run_calls_after_export(self):
        """ It should call _after_export when done """
        exporter = self._new_exporter(
            carepoint_id=self.carepoint_id,
            binding_record=self._new_record('2016-06-12 00:00:00'),
        )
        with mock.patch.object(exporter, '_should_import') as mk:
            mk.return_value = False
            with mock.patch.object(exporter, '_run'):
                with mock.patch.object(exporter.binder, 'bind'):
                    with mock.patch.object(exporter, '_after_export') as mk:
                        mk.side_effect = EndTestException
                        with self.assertRaises(EndTestException):
                            exporter.run(self.binding_id)

    def test__run_exception(self):
        """ Private run should not be implemented at this level """
        exporter = self._new_exporter()
        with self.assertRaises(NotImplementedError):
            exporter._run()

    def test_after_export(self):
        """ It should return None """
        exporter = self._new_exporter()
        res = exporter._after_export()
        self.assertEqual(None, res)
