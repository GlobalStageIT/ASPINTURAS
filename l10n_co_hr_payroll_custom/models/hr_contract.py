from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Campos funcionales Jorels y base de nómina'

    type_contract_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_contracts", string="Type contract", related='contract_type_id.type_contract_id')
    employee_type = fields.Selection(related='contract_type_id.employee_type')
