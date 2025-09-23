from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    type_concept = fields.Selection(related='salary_rule_id.type_concept')
    date_from = fields.Date(string="Date From", related='slip_id.date_from', store=True)
    date_to = fields.Date(string="Date To", related='slip_id.date_to', store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        """Function for compute total amount"""
        for line in self:
            if line.salary_rule_id.multiply_quantity:
                line.total = round(float(line.quantity) * line.amount * line.rate / 100)
            else:
                line.total = line.amount * line.rate / 100

    def _get_partner_id(self, credit_account, is_employee=False):
        """
        Get partner_id of slip line to use in account_move_line
        """
        res = super(HrPayslipLine, self)._get_partner_id(credit_account)
        if is_employee:
            return self.slip_id.employee_id.work_contact_id.id
        else:
            if self.salary_rule_id.register_id.partner_from_employee_contract:
                baselocaldict = {
                    'env': self.env,
                    'uid': self._uid,
                    'user': self.env.user,
                    'self': self,
                }
                field_name = self.salary_rule_id.register_id.field_id.name
                try:
                    partner_id = safe_eval(str('self.employee_id.' + field_name + '.id'), baselocaldict)
                except Exception as e:
                    raise ValidationError('Por favor configure los registros de contribucion \n Error: ' + str(e))
                return partner_id
            else:
                register_partner_id = self.salary_rule_id.register_id.partner_id
                partner_id = register_partner_id.id or self.slip_id.employee_id.work_contact_id.id
                if partner_id or register_partner_id:
                    return partner_id or register_partner_id

        return res
