from odoo import models, fields, api


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_vacation = fields.Boolean(string="Is Vacation")