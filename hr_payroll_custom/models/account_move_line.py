from odoo import models, fields, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payroll_type_rule = fields.Selection(selection=[('loan', 'Loan'),
                                                    ('savings', 'Savings'),
                                                    ('release', 'Release'),
                                                    ('garnishment', 'Garnishment'),
                                                    ('payroll', 'Payroll'),
                                                    ('contributor', 'Contributor'),
                                                    ('pila', 'PILA'),
                                                    ('severance', 'Severance'),
                                                    ('other', 'Other')],
                                         string='Salary Rule Type Payable', default='other')