from odoo import models, fields, api, _


class HrContractType(models.Model):
    _inherit = 'hr.contract.type'
    _description = 'Campos funcionales Jorels y base de nómina'

    type_contract_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_contracts", string="Type contract")
    employee_type = fields.Selection([
        ('employee', 'Employee'),
        ('student', 'Student'),
        ('trainee', 'Trainee'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelancer'),
    ], string='Employee Type', required=True,
        help="The employee type. Although the primary purpose may seem to categorize employees, this field has also an impact in the Contract History. Only Employee type is supposed to be under contract and will have a Contract History.")
