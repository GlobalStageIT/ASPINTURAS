from odoo import fields, models, api


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    payroll_period_id = fields.Many2one('hr.payroll.period', string="Period", required=True)
    type = fields.Many2one(comodel_name='hr.payslip.run.type', string='Type')

    @api.onchange('payroll_period_id')
    def _value_dates(self):
        for record in self:
            if record.payroll_period_id:
                record.date_start = record.payroll_period_id.date_start
                record.date_end = record.payroll_period_id.date_end
