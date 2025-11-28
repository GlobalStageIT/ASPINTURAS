from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    take_worked_days = fields.Boolean(string="Take Working Days", default=False)
    apply_dominican_discount = fields.Boolean(string="Aplica Dominican Discount")
    appears_leave = fields.Boolean(string="Appears Leave", default=False)
