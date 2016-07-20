# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# import mock

# from openerp.addons.connector_carepoint.unit.import_synchronizer import (
#     import_record,
# )

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.medical_pharmacy'


class TestMedicalPharmacy(SetUpCarepointBase):

    def setUp(self):
        super(TestMedicalPharmacy, self).setUp()
        self.BindModel = self.env['carepoint.medical.pharmacy']
        self.Model = self.env['medical.pharmacy']

    def _new_record(self, bind=True, name='Test Pharm'):
        vals = {'name': name}
        if bind:
            Model = self.BindModel
            vals.update({
                'carepoint_id': 1234567,
                'backend_id': self.backend.id,
            })
        else:
            Model = self.Model
        return Model.create(vals)

    # def test_import(self):
    #     """ It should import record """
    #     with self.mock_adapter() as api:
