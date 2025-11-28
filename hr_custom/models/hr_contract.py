from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    hourly_wage = fields.Float(string="Hourly Wage", help="Hourly salary for contractors or freelancers")
    employment_category = fields.Selection([
        ('employee', 'Employee'),
        ('student', 'Student'),
        ('trainee', 'Trainee'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelancer'),],
        string="type of fees",
        help="Category of employment",
        related="contract_type_id.employee_type",
    )
    adjunto_contract = fields.Binary(string="Contract",store=True)
    adjunto_contract_name = fields.Char(string="Contract name")

    @api.onchange('employment_category')
    def _onchange_employment_category(self):
        if self.employment_category:
            self.hourly_wage = 0.0
            self.wage = 0.0
