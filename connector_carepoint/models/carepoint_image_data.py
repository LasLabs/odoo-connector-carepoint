# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import BaseImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)

try:
    import magic
except ImportError:
    _logger.info('`python-magic` library is not installed.')


class CarepointImageData(models.Model):
    _name = 'carepoint.image.data'
    _description = 'CarePoint Image Data'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        string='Attachment',
        comodel_name='ir.attachment',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.image.data',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    image_type = fields.Selection(
        selection='_get_image_types',
    )
    samba_root = fields.Char()
    samba_path = fields.Char(
        compute='_compute_samba_path',
    )
    pharmacy_id = fields.Many2one(
        string='Pharmacy',
        comodel_name='medical.pharmacy',
    )
    patient_id = fields.Many2one(
        string='Patient',
        comodel_name='medical.patient',
    )
    related_carepoint_id = fields.Integer()

    @api.multi
    def _compute_samba_path(self):
        for record in self:
            record.samba_path = '%s/%s' % (
                record.samba_root, record.name,
            )

    @api.model
    def _get_image_types(self):
        """Return the image type references."""
        return [
            ('prescription', 'medical.prescription')
            ('unknown_3', 'unknown_3'),
            ('unknown_7', 'unknown_7'),
            ('unknown_1001', 'unknown_1001'),
        ]


class CarepointCarepointImageData(models.Model):
    _name = 'carepoint.carepoint.image.data'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.image.data': 'odoo_id'}
    _description = 'Carepoint CarepointImageData'
    _cp_lib = 'fdb_img'

    odoo_id = fields.Many2one(
        string='CarepointImageData',
        comodel_name='carepoint.image.data',
        required=True,
        ondelete='restrict'
    )


@carepoint
class CarepointImageDataAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.carepoint.image.data'


@carepoint
class CarepointImageDataBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint CarepointImageDatas.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.carepoint.image.data']


@carepoint
class CarepointImageDataImportMapper(BaseImportMapper):
    _model_name = 'carepoint.carepoint.image.data'
    direct = [
        (trim('FullFileName'), 'name'),
        (trim('RootFolderName'), 'samba_root'),
        ('data', 'datas'),
        ('image_type', 'image_type'),
        ('related_id', 'related_carepoint_id'),
    ]

    @mapping
    @only_create
    def mimetype(self, record):
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            return {'mimetype': m.id_buffer(record['data'])}

    @mapping
    @only_create
    def type(self, record):
        return {'type': 'binary'}

    @mapping
    @only_create
    def image_type(self, record):
        return {'image_type': record.image_type}

    @mapping
    def carepoint_id(self, record):
        carepoint_id = '%s,%s' % (record.image_type_cn, record.related_id)
        return {'carepoint_id': carepoint_id}


@carepoint
class CarepointImageDataImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.image.data']
    _base_mapper = CarepointImageDataImportMapper

    def _after_import(self, binding):
        """Update the attachment info with the record."""
        try:
            image_model = self.env[binding.image_type]
        except KeyError:
            return

        try:
            image_bind_model = self.env[
                image_model.carepoint_bind_ids._name
            ]
        except (AttributeError, KeyError):
            return

        bind_image = image_bind_model.search([
            ('carepoint_id', '=', binding.related_id),
        ],
            limit=1,
        )

        if not bind_image:
            return

        binding.write({
            'res_model': image_model._name,
            'res_id': bind_image.odoo_id.id,
            'res_field': bind_image._carepoint_image_field,
        })

    def _get_carepoint_data(self):
        """ Return the raw Carepoint data for ``self.carepoint_id`` """
        record = super(CarepointImageDataImporter, self)._get_carepoint_data()
        record.data = self.backend_adapter.read_image(
            record['image_path'],
        )
        return record
