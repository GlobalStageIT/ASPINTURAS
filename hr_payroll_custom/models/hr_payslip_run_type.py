from odoo import fields, models

class HrPayslipRunType(models.Model):
    _name = "hr.payslip.run.type"
    _description = "HR Payslip Run Type"

    name = fields.Char('Name', required=True)
    rule_ids = fields.Many2many('hr.salary.rule', string="Rules")
    company_id = fields.Many2one('res.company', string="Company")
