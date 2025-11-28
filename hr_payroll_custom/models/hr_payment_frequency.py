from odoo import fields, models, api, _


class HrPaymentFrequency(models.Model):
    _name = 'hr.payment.frequency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Frequencies of payroll periods'

    name = fields.Selection([('monthly', 'Mensual'), ('bi_weekly', 'Quincenal'), ('week', 'Semanal'), ('day', 'Días')],
                            string='Name', required=True)
    code = fields.Char(string='Code', readonly=True)

    @api.onchange('name')
    def _default_value_code(self):
        for record in self:
            if record.name:
                if record.name == 'monthly':
                    record.code = 'MON'
                if record.name == 'bi_weekly':
                    record.code = 'BI'
                if record.name == 'week':
                    record.code = 'WEEK'

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
         value = _(dict(self._fields['name'].selection).get(record.name))
         record.display_name = value
