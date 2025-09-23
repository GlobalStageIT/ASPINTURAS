from odoo import fields, models, api


class HrLeave(models.Model):
    _inherit = "hr.leave"

    payslip_worked_days_id = fields.Many2one('hr.payslip.worked.days', string="Payslip Worked Days")
    payslip_id = fields.Many2one('hr.payslip', string="Contract", required=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
    company_id = fields.Many2one('res.company', related='contract_id.company_id', store=True)
    is_extension = fields.Boolean(string="Is Extension", default=False)
    extension_leave_id = fields.Many2one('hr.leave', string="Is Extension", domain="[('holiday_status_id','=', holiday_status_id)]")

    @api.depends('date_from', 'date_to', 'resource_calendar_id', 'holiday_status_id.request_unit')
    def _compute_duration(self):
        durations = self._get_durations()
        for leave in self:
            days, hours = durations[leave.id]
            leave.number_of_hours = hours
            leave.number_of_days = days

            if not leave.holiday_status_id.take_worked_days:
                total_days = (leave.request_date_to - leave.request_date_from).days + 1
                leave.number_of_days = total_days
