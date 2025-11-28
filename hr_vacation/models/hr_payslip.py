from odoo import fields, models, _, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_vacation(self):
        vacation = self.env['hr.vacation'].search(
            [('employee_id', '=', self.employee_id.id), ('contract_id', '=', self.contract_id.id)])
        if not vacation:
            raise UserError(_("No vacation line found for the employee"))
        return vacation
