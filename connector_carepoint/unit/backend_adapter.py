# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from carepoint import Carepoint
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter


carepoints = {}


class CarepointCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for Carepoint """

    def __init__(self, connector_env):
        """ Ready the DB adapter
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(CarepointCRUDAdapter, self).__init__(connector_env)
        global carepoints  # @TODO: Better way to handle this
        backend = self.backend_record
        if carepoints.get(backend.server) is None:
            carepoints[backend.server] = Carepoint(
                server=backend.server,
                user=backend.username,
                passwd=backend.password,
                db_args={'drv': backend.db_driver},
            )
        self.carepoint = carepoints[backend.server]

    def __to_camel_case(self, snake_case):
        """ Convert the snake_case to CamelCase
        :param snake_case: To convert
        :type snake_case: str
        :rtype: str
        """
        parts = snake_case.split('_')
        return "".join(x.title() for x in parts)

    def __get_cp_model(self):
        """ Get the correct model object by name from Carepoint lib
        :rtype: :class:`sqlalchemy.schema.Table`
        """
        name = self.connector_env.model._cp_lib
        camel_name = self.__to_camel_case(name)
        return self.carepoint[camel_name]

    def search(self, **filters):
        """ Search table by filters and return record ids
        :param filters: Filters to apply to search
        :rtype: list
        """
        model_obj = self.__get_cp_model()
        pk = self.carepoint.get_pks(model_obj)[0]
        res = self.carepoint.search(model_obj, filters, [pk])
        return [getattr(row, pk) for row in res]

    def read(self, _id, attributes=None):
        """ Gets record by id and returns the object
        :param _id: Id of record to get from Db. Can be comma sep str
            for multiple indexes
        :type _id: mixed
        :param attributes: Attributes to rcv from db. None for *
        :type attributes: list or None
        :rtype: dict

        @TODO: Fix the conjoined index lookups, this is pretty flaky
        """
        # @TODO: Fix lookup by ident
        model_obj = self.__get_cp_model()
        pks = self.carepoint.get_pks(model_obj)
        domain = {}
        try:
            for idx, id_part in enumerate(_id.split(',')):
                domain[pks[idx]] = id_part
        except AttributeError:
            domain[pks[0]] = _id
        return self.carepoint.search(model_obj, domain, attributes)[0]

    def read_image(self, path):
        """ Returns an image resource from CarePoint

        Args:
            path: :type:`str` SMB path of image

        Returns:
            :type:`str` Binary string representation of file
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
        model_obj = self.__get_cp_model()
        return self.carepoint.search(model_obj, filters, attributes)

    def create(self, data):
        """ Wrapper to create a record on the external system
        :param data: Data to create record with
        :type data: dict
        :rtype: :class:`sqlalchemy.ext.declarative.Declarative`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.create(model_obj, data)

    def write(self, _id, data):
        """ Update record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :param data: Data to create record with
        :type data: dict
        :rtype: :class:`sqlalchemy.ext.declarative.Declarative`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.update(model_obj, _id, data)

    def delete(self, _id):
        """ Delete record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :rtype: bool
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.delete(model_obj, _id)
