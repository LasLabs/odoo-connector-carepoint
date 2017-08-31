# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from contextlib import contextmanager

from odoo.addons.connector_v9.unit.backend_adapter import CRUDAdapter

try:
    from sqlalchemy.exc import InvalidRequestError
    from sqlalchemy.exc import TimeoutError
except ImportError:
    pass

_logger = logging.getLogger(__name__)

try:
    from carepoint import Carepoint
except ImportError:
    _logger.info('Cannot import ``carepoint`` Python library.')


class CarepointCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for Carepoint """

    RECONNECT_EXCEPTIONS = [
        InvalidRequestError,
        TimeoutError,
    ]

    def __init__(self, connector_env):
        """ Ready the DB adapter
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(CarepointCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record
        self.carepoint = Carepoint(
            server=backend.server,
            user=backend.username,
            passwd=backend.password,
            db_args={'drv': backend.db_driver},
        )

    def __to_camel_case(self, snake_case):
        """ Convert the snake_case to CamelCase
        :param snake_case: To convert
        :type snake_case: str
        :rtype: str
        """
        parts = snake_case.split('_')
        return "".join(x.title() for x in parts)

    def _retry(method):
        """ It provides a decorator to handle retry/reconnects. """

        def retry(self, *args, **kwargs):

            try:
                return method(self, *args, **kwargs)
            except tuple(self.RECONNECT_EXCEPTIONS):
                self.carepoint._init_env(True)
                return method(self, *args, **kwargs)

        return retry

    @_retry
    def _get_cp_model(self):
        """ Get the correct model object by name from Carepoint lib
        :rtype: :class:`sqlalchemy.schema.Table`
        """
        name = self.connector_env.model._cp_lib
        camel_name = self.__to_camel_case(name)
        return self.carepoint[camel_name]

    @_retry
    def search(self, retry=True, **filters):
        """ Search table by filters and return record ids
        :param filters: Filters to apply to search
        :rtype: list of PKs. Multi PKs are joined with ","
        """
        model_obj = self._get_cp_model()
        pks = self.carepoint.get_pks(model_obj)
        res = self.carepoint.search(model_obj, filters, pks)
        return_vals = []
        for row in res:
            return_vals.append(
                ','.join('%s' % getattr(row, pk) for pk in pks)
            )
        return return_vals

    @_retry
    def read(self, _id, attributes=None, return_all=False):
        """ Gets record by id and returns the object
        :param _id: Id of record to get from Db. Can be comma sep str
            for multiple indexes
        :type _id: mixed
        :param attributes: Attributes to rcv from db. None for *
        :type attributes: list or None
        :rtype: :class:`sqlalchemy.engine.ResultProxy`

        @TODO: Fix the conjoined index lookups, this is pretty flaky
        """
        # @TODO: Fix lookup by ident
        model_obj = self._get_cp_model()
        pks = self.carepoint.get_pks(model_obj)
        domain = {}
        try:
            for idx, id_part in enumerate(_id.split(',')):
                domain[pks[idx]] = id_part
        except AttributeError:
            domain[pks[0]] = _id
        res = self.carepoint.search(model_obj, domain, attributes)
        try:
            return res if return_all else res[0]
        except IndexError:
            return None

    def read_image(self, path):
        """ Returns an image resource from CarePoint

        Args:
            path: :type:`str` SMB path of image

        Returns:
            :type:`str` Base64 encoded binary file
        """
        return self.carepoint.get_file(path).read().encode('base64')

    def write_image(self, path, file_obj):
        """ Write a file-like object to CarePoint SMB resource

        Args:
            path: :type:`str` SMB path to write to
            file_obj: :type:`file` File like object to send to server

        Returns:
            :type:`bool`
        """
        return self.carepoint.send_file(path, file_obj)

    def search_read(self, attributes=None, **filters):
        """ Search table by filters and return records
        :param attributes: Attributes to rcv from db. None for *
        :type attributes: list or None
        :param filters: Filters to apply to search
        :rtype: :class:`sqlalchemy.engine.ResultProxy`
        """
        model_obj = self._get_cp_model()
        return self.carepoint.search(model_obj, filters, attributes)

    @_retry
    def create(self, data):
        """ Wrapper to create a record on the external system
        Params:
            data: ``dict`` of Data to create record with
        Returns:
            ``str`` of external carepoint_id
        """
        model_obj = self._get_cp_model()
        pks = self.carepoint.get_pks(model_obj)
        out_pks = []
        for pk in pks:
            if not data.get(pk):
                data[pk] = self.carepoint.get_next_sequence(pk)
            out_pks.append(str(data[pk]))
        self.carepoint.create(model_obj, data)
        return ','.join(out_pks)

    def write(self, _id, data):
        """ Update record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :param data: Data to create record with
        :type data: dict
        :rtype: :class:`sqlalchemy.engine.ResultProxy`
        """
        record = self.read(_id, return_all=True)
        record.update(data)
        record.session.commit()
        return record

    def delete(self, _id):
        """ Delete record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :rtype: bool
        """
        model_obj = self._get_cp_model()
        return self.carepoint.delete(model_obj, _id)
