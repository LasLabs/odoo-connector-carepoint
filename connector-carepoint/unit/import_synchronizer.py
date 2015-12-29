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


"""
Importers for Carepoint.
An import can be skipped if the last sync date is more recent than
the last update in Carepoint.
They should call the ``bind`` method if the binder even if the records
are already bound, to update the last sync date.
"""


import logging
from openerp import fields, _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.exception import IDMissingInBackend
from ..backend import carepoint
from ..connector import get_environment, add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointImporter(Importer):
    """ Base importer for Carepoint """

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(CarepointImporter, self).__init__(connector_env)
        self.carepoint_id = None
        self.carepoint_record = None

    def _get_carepoint_data(self):
        """ Return the raw Carepoint data for ``self.carepoint_id`` """
        return self.backend_adapter.read(self.carepoint_id)

    def _before_import(self):
        """ Hook called before the import, when we have the Carepoint
        data"""

    def _is_uptodate(self, binding):
        """Return True if the import should be skipped because
        it is already up-to-date in Odoo"""
        assert self.carepoint_record
        if not self.carepoint_record.get('chg_date'):
            return  # no update date on Carepoint, always import it.
        if not binding:
            return  # it does not exist so it should not be skipped
        sync = binding.sync_date
        if not sync:
            return
        from_string = fields.Datetime.from_string
        sync_date = from_string(sync)
        carepoint_date = from_string(self.carepoint_record['updated_at'])
        # if the last synchronization date is greater than the last
        # update in carepoint, we skip the import.
        # Important: at the beginning of the exporters flows, we have to
        # check if the carepoint_date is more recent than the sync_date
        # and if so, schedule a new import. If we don't do that, we'll
        # miss changes done in Carepoint
        return carepoint_date < sync_date

    def _import_dependency(self, carepoint_id, binding_model,
                           importer_class=None, always=False):
        """ Import a dependency.
        The importer class is a class or subclass of
        :class:`CarepointImporter`. A specific class can be defined.
        :param carepoint_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :class:`odoo.addons.connector.\
                                     connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: CarepointImporter
        :type importer_cls: :class:`odoo.addons.connector.\
                                    connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on Carepoint since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not carepoint_id:
            return
        if importer_class is None:
            importer_class = CarepointImporter
        binder = self.binder_for(binding_model)
        if always or binder.to_odoo(carepoint_id) is None:
            importer = self.unit_for(importer_class, model=binding_model)
            importer.run(carepoint_id)

    def _import_dependencies(self):
        """ Import the dependencies for the record
        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~odoo.addons.connector.unit.mapper.MapRecord`
        """
        return self.mapper.map_record(self.carepoint_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct
        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.
        Raise `InvalidDataError`
        """
        return

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.
        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).
        If it returns None, the import will continue normally.
        :returns: None | str | unicode
        """
        return

    def _get_binding(self):
        return self.binder.to_odoo(self.carepoint_id, browse=True)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the Odoo record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug(
            '%d created from carepoint %s',
            binding,
            self.carepoint_id)
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an Odoo record """
        # special check on data before import
        self._validate_data(data)
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug(
            '%d updated from carepoint %s',
            binding,
            self.carepoint_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def run(self, carepoint_id, force=False):
        """ Run the synchronization
        :param carepoint_id: identifier of the record on Carepoint
        """
        self.carepoint_id = carepoint_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            carepoint_id,
        )
        # Keep a lock on this import until the transaction is committed
        self.advisory_lock_or_retry(lock_name)

        try:
            self.carepoint_record = self._get_carepoint_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in Carepoint')

        skip = self._must_skip()
        if skip:
            return skip

        binding = self._get_binding()

        if not force and self._is_uptodate(binding):
            return _('Already up-to-date.')
        self._before_import()

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        self.binder.bind(self.carepoint_id, binding)

        self._after_import(binding)


class BatchImporter(Importer):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            self._import_record(record_id)

    def _import_record(self, record_id):
        """ Import a record directly or delay the import of the record.
        Method to implement in sub-classes.
        """
        raise NotImplementedError


class DirectBatchImporter(BatchImporter):
    """ Import the records directly, without delaying the jobs. """
    _model_name = None

    def _import_record(self, record_id):
        """ Import the record directly """
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      record_id)


class DelayedBatchImporter(BatchImporter):
    """ Delay import of the records """
    _model_name = None

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record_id,
                            **kwargs)


@carepoint
class SimpleRecordImporter(CarepointImporter):
    """ Import one Carepoint Website """
    _model_name = [
        'carepoint.website',
        'carepoint.res.partner.category',
    ]


@carepoint
class TranslationImporter(Importer):
    """ Import translations for a record.
    Usually called from importers, in ``_after_import``.
    For instance from the products and products' categories importers.
    """

    _model_name = ['carepoint.product.category',
                   'carepoint.product.product',
                   ]

    def _get_carepoint_data(self, storeview_id=None):
        """ Return the raw Carepoint data for ``self.carepoint_id`` """
        return self.backend_adapter.read(self.carepoint_id, storeview_id)

    def run(self, carepoint_id, binding_id, mapper_class=None):
        self.carepoint_id = carepoint_id
        storeviews = self.env['carepoint.storeview'].search(
            [('backend_id', '=', self.backend_record.id)]
        )
        default_lang = self.backend_record.default_lang_id
        lang_storeviews = [sv for sv in storeviews
                           if sv.lang_id and sv.lang_id != default_lang]
        if not lang_storeviews:
            return

        # find the translatable fields of the model
        fields = self.model.fields_get()
        translatable_fields = [field for field, attrs in fields.iteritems()
                               if attrs.get('translate')]

        if mapper_class is None:
            mapper = self.mapper
        else:
            mapper = self.unit_for(mapper_class)

        binding = self.model.browse(binding_id)
        for storeview in lang_storeviews:
            lang_record = self._get_carepoint_data(storeview.carepoint_id)
            map_record = mapper.map_record(lang_record)
            record = map_record.values()

            data = dict((field, value) for field, value in record.iteritems()
                        if field in translatable_fields)

            binding.with_context(connector_no_export=True,
                                 lang=storeview.lang_id.code).write(data)


@carepoint
class AddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the underlying model
    (not the carepoint.* but the _inherits'ed model) """

    _model_name = ['carepoint.product.product',
                   'carepoint.product.category',
                   ]

    def run(self, odoo_binding_id):
        binding = self.model.browse(odoo_binding_id)
        record = binding.odoo_id
        add_checkpoint(self.session,
                       record._model._name,
                       record.id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def import_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch import of records from Carepoint """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImporter)
    importer.run(filters=filters)


@job(default_channel='root.carepoint')
def import_record(session, model_name, backend_id, carepoint_id, force=False):
    """ Import a record from Carepoint """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(CarepointImporter)
    importer.run(carepoint_id, force=force)
