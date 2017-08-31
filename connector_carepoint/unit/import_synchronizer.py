# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


"""
Importers for Carepoint.
An import can be skipped if the last sync date is more recent than
the last update in Carepoint.
They should call the ``bind`` method if the binder even if the records
are already bound, to update the last sync date.
"""


import logging
from odoo import fields, _
from odoo.addons.connector_v9.queue.job import job
from odoo.addons.connector_v9.connector import ConnectorUnit
from odoo.addons.connector_v9.unit.synchronizer import Importer
from ..backend import carepoint
from ..connector import get_environment, add_checkpoint


_logger = logging.getLogger(__name__)


def int_or_str(val):
    try:
        return int(val)
    except:
        return str(val)


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
        _logger.debug('Getting CP data for %s', self.carepoint_id)
        return self.backend_adapter.read(self.carepoint_id)

    def _before_import(self):
        """ Hook called before the import, when we have the Carepoint
        data"""

    def _is_current(self, binding):
        """Return True if the import should be skipped because
        it is already up-to-date in Odoo"""
        if not self.carepoint_record:
            raise AssertionError(_(
                'No carepoint record to import.',
            ))
        if not self.carepoint_record.get('chg_date'):
            return  # no update date on Carepoint, always import it.
        if not binding:
            return  # it does not exist so it should not be skipped
        sync = binding.sync_date
        if not sync:
            return
        from_string = fields.Datetime.from_string
        sync_date = from_string(sync)
        carepoint_date = self.carepoint_record.get('chg_date')
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
        :param importer_cls: :class:`odoo.addons.connector_v9.\
                                     connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: CarepointImporter
        :type importer_cls: :class:`odoo.addons.connector_v9.\
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
        :py:class:`~odoo.addons.connector_v9.unit.mapper.MapRecord`
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
        return self.binder.to_odoo(self.carepoint_id,
                                   unwrap=False,
                                   browse=True)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the Odoo record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(
            connector_no_export=True,
            id_no_validate=True,
            rx_no_validate=True,
        )
        _logger.debug('Creating with %s', data)
        binding = model.create(data)
        _logger.debug(
            '%d created from carepoint %s',
            binding,
            self.carepoint_id,
        )
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an Odoo record """
        # special check on data before import
        self._validate_data(data)
        model = binding.with_context(
            connector_no_export=True,
            id_no_validate=True,
            rx_no_validate=True,
        )
        model.write(data)
        _logger.debug(
            '%d updated from carepoint %s',
            binding,
            self.carepoint_id,
        )
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def _enforce_user_exists(self):
        """ It is called for every export, enforcing user exists in CarePoint

        No user should be able to write or create data in Odoo without an
        account. This is enforced here by importing the create and write
        user.
        """
        if self.model._name == 'carepoint.res.users':
            return
        try:
            if self.carepoint_record['add_user_id']:
                import_record(
                    self.session,
                    'carepoint.res.users',
                    self.backend_record.id,
                    self.carepoint_record['add_user_id'],
                )
        except KeyError:
            pass
        try:
            if self.carepoint_record['chg_user_id']:
                import_record(
                    self.session,
                    'carepoint.res.users',
                    self.backend_record.id,
                    self.carepoint_record['chg_user_id'],
                )
        except KeyError:
            pass

    def run(self, carepoint_id, force=False):
        """ Run the synchronization
        :param carepoint_id: identifier of the record on Carepoint
        """
        self.carepoint_id = carepoint_id
        self.carepoint_record = self._get_carepoint_data()
        _logger.debug('self.carepoint_record - %s', self.carepoint_record)
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            carepoint_id,
        )
        # Keep a lock on this import until the transaction is committed
        self.advisory_lock_or_retry(lock_name)

        skip = self._must_skip()
        if skip:
            return skip

        binding = self._get_binding()

        if not force and self._is_current(binding):
            return _('Already Up To Date.')
        self._before_import()

        # Enforce user existance on local
        self._enforce_user_exists()

        # import user dependencies if the model has them
        try:
            self._import_user_dependencies()
        except AttributeError:
            pass

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()
        _logger.debug('Mapped to %s', map_record)

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
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        _logger.info('Search for carepoint companies %s returned %s\n',
                     filters, record_ids)
        for record_id in record_ids:
            _logger.info('In record loop with %s', record_id)
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
                      int_or_str(record_id))


class DelayedBatchImporter(BatchImporter):
    """ Delay import of the records """
    _model_name = None

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            int_or_str(record_id),
                            **kwargs)


@carepoint
class SimpleRecordImporter(CarepointImporter):
    """ Import one Carepoint Store """
    _model_name = [
        'carepoint.store',
    ]


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
                       record._name,
                       record.id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def import_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch import of records from Carepoint """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(DelayedBatchImporter)
    importer.run(filters=filters)


@job(default_channel='root.carepoint')
def import_record(session, model_name, backend_id, carepoint_id, force=False):
    """ Import a record from Carepoint """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(CarepointImporter)
    _logger.debug('Importing CP Record %s from %s', carepoint_id, model_name)
    importer.run(carepoint_id, force=force)
