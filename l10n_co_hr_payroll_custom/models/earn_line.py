from odoo import fields, models, api, _


class EarnLine(models.Model):
    _inherit = 'l10n_co_hr_payroll.earn.line'

    code = fields.Char(help="The code that can be used in the salary rules")
    quantity = fields.Float("Quantity", default=1)
    total = fields.Float("Total")
    rule_input_id = fields.Many2one('hr.rule.input', string='Rule input', copy=True, required=False,
                                    domain=[('input_id.type_concept', '=', 'earn')])
