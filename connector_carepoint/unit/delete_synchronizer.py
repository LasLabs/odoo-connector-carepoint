# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment


class CarepointDeleter(Deleter):
    """ Base deleter for Carepoint """

    def run(self, carepoint_id):
        """
        Run the synchronization, delete the record on Carepoint
        :param carepoint_id: identifier of the record to delete
        """
        raise NotImplementedError('Cannot delete records from CarePoint.')
        # self.backend_adapter.delete(carepoint_id)
        # return _('Record %s deleted on Carepoint') % carepoint_id


@job(default_channel='root.carepoint')
def export_delete_record(session, model_name, backend_id, carepoint_id):
    """ Delete a record on Carepoint """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(CarepointDeleter)
    return deleter.run(carepoint_id)
