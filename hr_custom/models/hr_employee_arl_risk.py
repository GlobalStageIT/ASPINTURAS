from odoo import models, fields


class HrEmployeeArlRisk(models.Model):
    _name = "hr.employee.arl.risk"
    _description = "HR Employee ARL Risk"

    name = fields.Char('Name')
    contribution_percentage = fields.Float(string="Contribution %", digits=(16, 3))
