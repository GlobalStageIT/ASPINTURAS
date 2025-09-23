from odoo import fields, _, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    coach_id = fields.Many2one(comodel_name='hr.employee', string='Coach',related='employee_id.coach_id')