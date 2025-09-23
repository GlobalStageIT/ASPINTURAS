from odoo import models, fields, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    group_payslip = fields.Boolean(string="Grouped in Payslip", default=False)
    debit_account_payslip = fields.Many2one('account.account', string="Debit Account Payslip")
