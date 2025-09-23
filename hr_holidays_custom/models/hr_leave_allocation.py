from odoo import fields, models


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
