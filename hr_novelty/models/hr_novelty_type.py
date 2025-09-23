from odoo import models, fields


class HrNoveltyType(models.Model):
    _name = 'hr.novelty.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payroll Novelty Type'

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    type = fields.Selection([('income', 'Income'), ('deduction', 'Deduction')], string='Type', required=True,
                            tracking=True)
    apply_factor = fields.Boolean(string='Apply Factor', tracking=True)
    factor = fields.Float(string='Factor', tracking=True)
    self_calculating = fields.Boolean(string="Self Calculating", tracking=True)
    type_calculation = fields.Selection([('days', 'Days'), ('hours', 'Hours')], string='Type Calculation',
                                        tracking=True)
    apply_date_end = fields.Boolean(string='Apply Date End', default=False, tracking=True)
    apply_quantity = fields.Boolean(string='Apply Quantity', default=False, tracking=True)
    take_ns = fields.Boolean(string='Take Not Salary', default=False, tracking=True)
    formula = fields.Html(string='Formula')
