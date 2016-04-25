# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.unit.mapper import mapping, ImportMapper


def trim(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Trim whitespace from field value
    Example::
        direct = [(trim('source'), 'target')]
    :param field: name of the source field in the record
    """
    def modifier(self,  record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return str(value).strip()
    return modifier


def to_float(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Convert SQLAlchemy Decimal types to float
    Example::
        direct = [(to_float('source'), 'target')]
    :param field: name of the source field in the record
    """
    def modifier(self,  record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return float(value)
    return modifier


def to_int(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Convert SQLAlchemy Decimal types to integer
    Example::
        direct = [(to_int('source'), 'target')]
    :param field: name of the source field in the record
    """
    def modifier(self,  record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return int(value)
    return modifier


class CarepointImportMapper(ImportMapper):
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class PersonImportMapper(CarepointImportMapper):

    def _get_name(self, record):
        name = []
        parts = ['fname', 'lname']
        for part in parts:
            if record.get(part):
                name.append(record[part])
        return ' '.join(name).title()

    @mapping
    def name(self, record):
        return {'name': self._get_name(record)}
