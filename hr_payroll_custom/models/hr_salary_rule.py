from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    type_concept = fields.Selection([
        ('earn', 'Earn'),
        ('deduction', 'Deduction'),
        ('other', 'Other')
    ], string="Type concept", default="other")
    specific_struct_salary_ids = fields.One2many(comodel_name='specific.causation', inverse_name='rule_id',
                                                 string="Causación especifica según estructura salarial")
    multiple_lines = fields.Boolean(string="Multiple Lines", default=False)
    multiply_quantity = fields.Boolean(string="Multiply Quantity", default=True)
    payroll_type_rule = fields.Selection(selection=[('loan', 'Loan'),
                                                    ('savings', 'Savings'),
                                                    ('release', 'Release'),
                                                    ('garnishment', 'Garnishment'),
                                                    ('payroll', 'Payroll'),
                                                    ('contributor', 'Contributor'),
                                                    ('pila', 'PILA'),
                                                    ('other', 'Other')],
                                         string='Salary Rule Type Payable', default='other', tracking=True)

    def _satisfy_condition(self, localdict):

        payslip_run_id = localdict.get('payslip').payslip_run_id
        if bool(payslip_run_id and payslip_run_id.type) and not (self in payslip_run_id.type.rule_ids):
            return False

        return super(HrSalaryRule, self)._satisfy_condition(localdict)