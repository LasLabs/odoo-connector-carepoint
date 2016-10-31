# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               changed_by,
                                               ImportMapper,
                                               ExportMapper,
                                               )


def trim(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Trim whitespace from field value
    Example::
        direct = [(trim('source'), 'target')]
    :param field: name of the source field in the record
    """

    def modifier(self, record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return str(value).strip()
    return modifier


def trim_and_titleize(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Trim whitespace from field value & title case
    Example::
        direct = [(trim_and_titleize('source'), 'target')]
    :param field: name of the source field in the record
    """

    def modifier(self, record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return str(value).strip().title()
    return modifier


def to_float(field):
    """ A modifier intended to be used on the ``direct`` mappings.
    Convert SQLAlchemy Decimal types to float
    Example::
        direct = [(to_float('source'), 'target')]
    :param field: name of the source field in the record
    """

    def modifier(self, record, to_attr):
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

    def modifier(self, record, to_attr):
        value = record.get(field)
        if not value:
            return False
        return int(value)
    return modifier


def add_to(field, number):
    """ A modifier intended to be used on the ``direct`` mappings.
    Add a number to the field value
    Example::
        direct = [(add_to('source', 1.5), 'target')]
    :param field: (str) name of the source field in the record
    :param number: (float|int) Number to add to source value
    """

    def modifier(self, record, to_attr):
        value = record[field]
        return float(value) + number
    return modifier


class CarepointImportMapper(ImportMapper):

    def _get_user(self, external_id, browse=False):
        """ It returns the Odoo user for the Carepoint external ID """
        binder = self.binder_for('carepoint.res.users')
        return binder.to_odoo(external_id, browse)

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    @only_create
    def create_uid(self, record):
        try:
            return {'create_uid': self._get_user(record['add_user_id'])}
        except KeyError:
            return

    @mapping
    def write_uid(self, record):
        try:
            return {'write_uid': self._get_user(record['chg_user_id'])}
        except KeyError:
            return

    @mapping
    @only_create
    def create_date(self, record):
        try:
            return {'create_date': record['add_date']}
        except KeyError:
            return

    @mapping
    def create_date(self, record):
        try:
            return {'write_date': record['chg_date']}
        except KeyError:
            return


class PartnerImportMapper(CarepointImportMapper):

    @mapping
    def tz(self, record):
        return {'tz': self.backend_record.default_tz}

    @mapping
    def currency_id(self, record):
        return {'currency_id': self.backend_record.company_id.currency_id.id}

    @mapping
    def property_account_payable_id(self, record):
        return {
            'property_account_payable_id':
                self.backend_record.default_account_payable_id.id,
        }

    @mapping
    def property_payment_term_id(self, record):
        return {
            'property_payment_term_id':
                self.backend_record.default_customer_payment_term_id.id,
        }

    @mapping
    def property_supplier_payment_term_id(self, record):
        return {
            'property_supplier_payment_term_id':
                self.backend_record.default_supplier_payment_term_id.id,
        }

    @mapping
    def property_account_receivable_id(self, record):
        return {
            'property_account_receivable_id':
                self.backend_record.default_account_receivable_id.id,
        }


class PersonImportMapper(PartnerImportMapper):

    def _get_name(self, record):
        # @TODO: Support other name parts (surname)
        name = []
        parts = ['fname', 'lname']
        for part in parts:
            if record.get(part):
                name.append(record[part])
        return ' '.join(name).title()

    @mapping
    def name(self, record):
        return {'name': self._get_name(record)}


class PersonExportMapper(ExportMapper):

    @mapping
    @changed_by('name')
    def names(self, record):
        # @TODO: Support other name parts (surname)
        if ' ' in record.name:
            parts = record.name.split(' ', 1)
            fname = parts[0]
            lname = parts[1]
        else:
            fname = '-'
            lname = record.name
        return {'lname': lname,
                'fname': fname,
                }


class CommonDateExportMapperMixer(object):
    """ It provides a mixer for add and change date / user mappers """

    def _get_user(self, user):
        """ It returns the Carepoint external ID for the Odoo user """
        binder = self.binder_for('carepoint.res.users')
        return binder.to_backend(user)

    @mapping
    @changed_by('create_uid')
    def add_user_id(self, record):
        return {'add_user_id': self._get_user(record.create_uid)}

    @mapping
    @changed_by('create_date')
    def add_date(self, record):
        return {'add_date': fields.Datetime.from_string(record.create_date)}

    @mapping
    @changed_by('write_uid')
    def chg_user_id(self, record):
        return {'chg_user_id': self._get_user(record.write_uid)}

    @mapping
    @changed_by('write_date')
    def chg_date(self, record):
        return {'chg_date': fields.Datetime.from_string(record.write_date)}
