from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    type_contracts_provision = fields.Many2many('hr.contract.type', string='Type Contracts Provision')
    type_leave_vacation = fields.Many2one('hr.leave.type', string='Type Leave Vacation')
    type_novelty_vacation = fields.Many2one('hr.novelty.type', string='Type Novelty Vacation Compensated')
