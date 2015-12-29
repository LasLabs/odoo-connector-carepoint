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


from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment


class CarepointDeleter(Deleter):
    """ Base deleter for Carepoint """

    def run(self, carepoint_id):
        """
        Run the synchronization, delete the record on Carepoint
        :param carepoint_id: identifier of the record to delete
        """
        self.backend_adapter.delete(carepoint_id)
        return _('Record %s deleted on Carepoint') % carepoint_id


@job(default_channel='root.carepoint')
def export_delete_record(session, model_name, backend_id, carepoint_id):
    """ Delete a record on Carepoint """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(CarepointDeleter)
    return deleter.run(carepoint_id)
