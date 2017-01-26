# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.unit import backend_adapter

from .common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.unit.backend_adapter'


class TestBackendAdapter(SetUpCarepointBase):

    def setUp(self):
        super(TestBackendAdapter, self).setUp()
        self.Model = backend_adapter.CarepointCRUDAdapter

    def _init_model(self, model='carepoint.carepoint.store'):
        self.model = self.env[model]
        self.api_camel = self.__to_camel_case(self.model._cp_lib)
        return self.Model(self.get_carepoint_helper(model))

    def __to_camel_case(self, snake_case):
        """ Convert the snake_case to CamelCase
        :param snake_case: To convert
        :type snake_case: str
        :rtype: str
        """
        parts = snake_case.split('_')
        return "".join(x.title() for x in parts)

    def test_init_new_connection(self):
        """ It should initialize a new connection when none for backend """
        with self.mock_api() as api:
            self._init_model()
            api.assert_called_once_with(
                server=self.backend.server,
                user=self.backend.username,
                passwd=self.backend.password,
                db_args={'drv': self.backend.db_driver},
            )

    def test_init_assigns_instance(self):
        """ It should assign carepoint instance variable during init """
        with self.mock_api() as api:
            expect = 'expect'
            api.return_value = expect
            res = self._init_model()
            self.assertEqual(expect, res.carepoint)

    def test_get_cp_model_resets(self):
        """ It should guard a reconnectable exception and clear globals """
        with self.mock_api():
            model = self._init_model()
            model.carepoint = mock.MagicMock()
            model.carepoint.__getitem__.side_effect = [
                model.RECONNECT_EXCEPTIONS[0],
            ]
            model.carepoint._init_env.side_effect = self.EndTestException
            with self.assertRaises(self.EndTestException):
                model.search()

    def test_get_cp_model_recurse(self):
        """ It should recurse when reconnectable exception is identified """
        with self.mock_api():
            model = self._init_model()
            model.carepoint = mock.MagicMock()
            model.carepoint.__getitem__.side_effect = [
                model.RECONNECT_EXCEPTIONS[0],
                self.EndTestException,
            ]
            with self.assertRaises(self.EndTestException):
                model.search()

    def test_get_cp_model_raise(self):
        """ It should guard a reconnectable exception and clear globals """
        with self.mock_api():
            model = self._init_model()
            model.carepoint = mock.MagicMock()
            model.carepoint.__getitem__.side_effect = [
                model.RECONNECT_EXCEPTIONS[0],
                model.RECONNECT_EXCEPTIONS[0],
            ]
            with self.assertRaises(model.RECONNECT_EXCEPTIONS[0]):
                model.search()

    def test_search_gets_pks(self):
        """ It should get the primary keys of the db """
        with self.mock_api() as api:
            expect = {
                'col1': 'Test',
                'col2': 1234,
            }
            self._init_model().search(**expect)
            api().get_pks.assert_called_once_with(
                api()[self.api_camel]
            )

    def test_search_does_search(self):
        """ It should search w/ filters and PK """
        with self.mock_api() as api:
            expect = {
                'col1': 'Test',
                'col2': 1234,
            }
            self._init_model().search(**expect)
            api().search.assert_called_once_with(
                api()[self.api_camel],
                expect,
                [api().get_pks().__getitem__()],
            )

    def test_read_gets_pks(self):
        """ It should get the primary keys of the db """
        with self.mock_api() as api:
            expect = 5
            self._init_model().read(expect)
            api().get_pks.assert_called_once_with(
                api()[self.api_camel]
            )

    def test_read_searches(self):
        """ It should search for ID w/ attributes """""
        with self.mock_api() as api:
            attr_expect = ['col1', 'col2']
            pk_expect = ['pk1', 'pk2']
            id_expect = '123,456'
            api().get_pks.return_value = pk_expect
            self._init_model().read(id_expect, attr_expect)
            api().search.assert_called_once_with(
                api()[self.api_camel],
                dict(zip(pk_expect, id_expect.split(','))),
                attr_expect,
            )

    def test_read_returns_first(self):
        """ It should return first record result """""
        with self.mock_api() as api:
            res = self._init_model().read(123, ['expect', 'no_expect'])
            self.assertEqual(api().search()[0], res)

    def test_read_returns_all(self):
        """ It should return first record result """""
        with self.mock_api() as api:
            res = self._init_model().read(123, ['expect', 'no_expect'], True)
            self.assertEqual(api().search(), res)

    def test_read_image_gets_file(self):
        """ It should get proper file path from server """
        with self.mock_api() as api:
            expect = '/path/to/obj'
            self._init_model().read_image(expect)
            api().get_file.assert_called_once_with(expect)

    def test_read_image_encodes_file_obj(self):
        """ It should base64 encode the resulting file obj """
        with self.mock_api() as api:
            self._init_model().read_image('/path/to/obj')
            api().get_file().read().encode.assert_called_once_with(
                'base64',
            )

    def test_read_image_returns_encoded_file(self):
        """ It should return the encoded file string """
        with self.mock_api() as api:
            res = self._init_model().read_image('/path/to/obj')
            self.assertEqual(
                api().get_file().read().encode(), res,
            )

    def test_write_image_sends_file(self):
        """ It should send file obj to proper path on server """
        with self.mock_api() as api:
            expect = ['path', 'file']
            self._init_model().write_image(*expect)
            api().send_file.assert_called_once_with(*expect)

    def test_write_image_returns_result(self):
        """ It should send file obj to proper path on server """
        with self.mock_api() as api:
            res = self._init_model().write_image('path', 'file')
            self.assertEqual(api().send_file(), res)

    def test_search_read_searches(self):
        """ It should search for ID w/ attributes """""
        with self.mock_api() as api:
            attr_expect = ['col1', 'col2']
            filter_expect = {'col4': 1234, 'col8': 'test'}
            self._init_model().search_read(attr_expect, **filter_expect)
            api().search.assert_called_once_with(
                api()[self.api_camel],
                filter_expect,
                attr_expect,
            )

    def test_search_read_returns_result(self):
        """ It should return result of search """""
        with self.mock_api() as api:
            attr_expect = ['col1', 'col2']
            filter_expect = {'col4': 1234, 'col8': 'test'}
            res = self._init_model().search_read(attr_expect, **filter_expect)
            self.assertEqual(api().search(), res)

    def test_create_creates(self):
        """ It should create w/ proper vals """
        with self.mock_api() as api:
            expect = {'data': 'test', 'col': 12323423}
            self._init_model().create(expect)
            api().create.assert_called_once_with(
                api()[self.api_camel],
                expect,
            )

    def test_create_gets_pks(self):
        """ It should get primary keys of model """
        with self.mock_api() as api:
            model = self._init_model()
            model.create({'data': 'test', 'col': 12323423})
            api().get_pks.assert_called_once_with(
                api()[self.api_camel],
            )

    def test_create_gets_sequences(self):
        """ It should get next sequence for PK """
        expect = mock.MagicMock()
        with self.mock_api() as api:
            model = self._init_model()
            api().get_pks.return_value = [expect]
            model.create({'data': 'test', 'col': 12323423})
            api().get_next_sequence.assert_called_once_with(
                expect,
            )

    def test_create_returns_pks(self):
        """ It should return comma joined PKs of new record """
        expect = ['col', 'no_exist']
        with self.mock_api() as api:
            model = self._init_model()
            api().get_pks.return_value = expect
            expect = {'data': 'test', 'col': 12323423}
            res = model.create(expect)
            self.assertEqual(
                '%s,%s' % (
                    str(expect['col']),
                    api().get_next_sequence(),
                ),
                res,
            )

    def test_delete_deletes(self):
        """ It should delete w/ proper vals """
        with self.mock_api() as api:
            expect = 123
            self._init_model().delete(expect)
            api().delete.assert_called_once_with(
                api()[self.api_camel],
                expect,
            )

    def test_delete_returns_result(self):
        """ It should return result of delete operation """
        with self.mock_api() as api:
            res = self._init_model().delete(123)
            self.assertEqual(api().delete(), res)

    def test_write_reads(self):
        """ It should get record for id """
        expect1, expect2 = 123, {'test': 'TEST'}
        with self.mock_api():
            model = self._init_model()
            with mock.patch.object(model, 'read') as read:
                model.write(expect1, expect2)
                read.assert_called_once_with(
                    expect1,
                    return_all=True,
                )

    def test_write_updates(self):
        """ It should update record w/ data """
        expect1, expect2 = 123, {'test': 'TEST'}
        with self.mock_api() as api:
            self._init_model().write(expect1, expect2)
            api().search().update.assert_called_once_with(
                expect2,
            )

    def test_write_commits(self):
        """ It should commit update to session """
        expect1, expect2 = 123, {'test': 'TEST'}
        with self.mock_api() as api:
            self._init_model().write(expect1, expect2)
            api().search().session.commit.assert_called_once_with()

    def test_write_returns(self):
        """ It should return record object """
        expect1, expect2 = 123, {'test': 'TEST'}
        with self.mock_api() as api:
            res = self._init_model().write(expect1, expect2)
            self.assertEqual(
                api().search(),
                res
            )
