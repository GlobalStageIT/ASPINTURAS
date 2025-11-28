from odoo import fields, models, api, _


class DeductionLine(models.Model):
    _inherit = 'l10n_co_hr_payroll.deduction.line'

    code = fields.Char(help="The code that can be used in the salary rules")
    rule_input_id = fields.Many2one('hr.rule.input', string='Rule input', copy=True, required=False)