# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import socket
import logging
import xmlrpclib

from carepoint import Carepoint
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from openerp.addons.connector.exception import (NetworkRetryableError,
                                                RetryableJobError)

from datetime import datetime
_logger = logging.getLogger(__name__)


recorder = {}


def call_to_key(method, arguments):
    """ Used to 'freeze' the method and arguments of a call to Carepoint
    so they can be hashable; they will be stored in a dict.
    Used in both the recorder and the tests.
    """
    def freeze(arg):
        if isinstance(arg, dict):
            items = dict((key, freeze(value)) for key, value
                         in arg.iteritems())
            return frozenset(items.iteritems())
        elif isinstance(arg, list):
            return tuple([freeze(item) for item in arg])
        else:
            return arg

    new_args = []
    for arg in arguments:
        new_args.append(freeze(arg))
    return (method, tuple(new_args))


def record(method, arguments, result):
    """ Utility function which can be used to record test data
    during synchronisations. Call it from CarepointCRUDAdapter._call
    Then ``output_recorder`` can be used to write the data recorded
    to a file.
    """
    recorder[call_to_key(method, arguments)] = result


def output_recorder(filename):
    import pprint
    with open(filename, 'w') as f:
        pprint.pprint(recorder, f)
    _logger.debug('recorder written to file %s', filename)


class CarepointCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for Carepoint """

    def __init__(self, connector_env, ):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(CarepointDbAdapter, self).__init__(connector_env)
        backend = self.backend_record
        self.carepoint = Carepoint(
            server=backend.server,
            user=backend.username,
            passwd=backend.password,
        )
        
    def __to_camel_case(self, snake_case, ):
        """
        Convert the snake_case to CamelCase
        :param snake_case: To convert
        :type snake_case: str
        :rtype: str
        """
        parts = snake_case.split('_')
        return "".join(x.title() for x in components)
        
    def __get_cp_model(self, ):
        """
        Get the correct model object by name from Carepoint lib
        :rtype: :class:`sqlalchemy.schema.Table`
        """
        name = self.connector_env.model._cp_lib
        camel_name = self.__to_camel_case(name)
        return getattr(self.carepoint, camel_name)

    def search(self, filters=None, ):
        """
        Search table by filters and return records
        :param filters: Filters to apply to search
        :type filters: dict or None
        :rtype: :class:`sqlalchemy.engine.ResultProxy`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.search(model_obj, filters)

    def read(self, _id, attributes=None, ):
        """
        Gets record by id and returns the object
        :param _id: Id of record to get from Db
        :type _id: int
        :param attributes: Attributes to rcv from db. None for *
        :type attributes: list or None
        :rtype: :class:`sqlalchemy.engine.ResultProxy`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.read(model_obj, _id)

    def create(self, data, ):
        """
        Wrapper to create a record on the external system
        :param data: Data to create record with
        :type data: dict
        :rtype: :class:`sqlalchemy.ext.declarative.Declarative`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.create(model_obj, data)

    def write(self, _id, data, ):
        """
        Update record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :param data: Data to create record with
        :type data: dict
        :rtype: :class:`sqlalchemy.ext.declarative.Declarative`
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.update(model_obj, _id, data)

    def delete(self, _id, ):
        """
        Delete record on the external system
        :param _id: Id of record to manipulate
        :type _id: int
        :rtype: bool
        """
        model_obj = self.__get_cp_model()
        return self.carepoint.delete(model_obj, _id)
