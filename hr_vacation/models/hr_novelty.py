from odoo import fields, _, models, api
from odoo.exceptions import UserError


class HrNovelty(models.Model):
    _inherit = "hr.novelty"

    is_vacation_compensated = fields.Boolean(related='novelty_type_id.is_vacation_compensated')
    contract_food_aid = fields.Monetary(related='contract_id.food_aid', string="Auxilio No Salarial")
    form_vacation = fields.Binary(string="Form Vacation")
    form_vacation_name = fields.Char(string="Form Vacation Name")
    ns_value = fields.Float(string="Not Salary Value", default=0)
    s_value = fields.Float(string="Salary Value", default=0)
    total_compensated = fields.Float(string="Total")
    novelty_id = fields.Many2one('hr.novelty', string="Novelty Ids")

    def novelty_preview(self):
        return {
            'name': _('Compensated Money Vacation'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.novelty',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.novelty_id.id,
        }

    @api.model
    def default_get(self, fields_list):
        res = super(HrNovelty, self).default_get(fields_list)
        if self.env.context.get('is_vacation_compensated'):
            res['employee_id'] = self.env.user.employee_id.id
            res['novelty_type_id'] = self.env['hr.novelty.type'].search([('is_vacation_compensated', '=', True)],
                                                                        limit=1).id
        return res

    def get_vacation(self, employee, contract):
        vacation = self.env['hr.vacation'].search(
            [('employee_id', '=', employee.id), ('contract_id', '=', contract.id)])
        return vacation

    @api.constrains('novelty_type_id')
    def validate_compensated(self):
        for record in self:
            if record.is_vacation_compensated:
                vacation = record.get_vacation(record.employee_id, record.contract_id)
                if record.quantity > vacation.balance / 2:
                    raise UserError(
                        _("Vacation compensated in cash may not exceed 50% of the days accrued, currently accrued {"
                          "0:.3f}.").format(
                            vacation.balance))

    @api.onchange('quantity')
    @api.constrains('quantity')
    def self_calculating(self):
        for record in self:
            if record.novelty_type_id.is_vacation_compensated and record.quantity != 0:

                vacation = record.get_vacation(record.employee_id, record.contract_id)
                if vacation.balance > 15:
                    if record.quantity > vacation.balance / 2:
                        raise UserError(
                            _("Las vacaciones compensadas en metálico no podrán superar el 50% de los días devengados, actualmente devengados {0:.3f}.").format(
                                vacation.balance))
                else:
                    raise UserError(
                        _("Las vacaciones compensadas no podrán solicitarse antes de que haya transcurrido un año."))

                value = record.contract_id.food_aid if record.novelty_type_id.take_ns else record.contract_id.wage
                ns_value = record.contract_id.food_aid
                if record.novelty_type_id.self_calculating:
                    if record.type_calculation == 'days':
                        record.value = (value / 30) * record.quantity
                        record.ns_value = (ns_value / 30) * record.quantity
                    elif record.type_calculation == 'hours':
                        record.value = (
                                (value / record.contract_id.resource_calendar_id.monthly_hours) * record.quantity)
                        record.ns_value = (
                                (ns_value / record.contract_id.resource_calendar_id.monthly_hours) * record.quantity)
                if record.novelty_type_id.apply_factor:
                    record.value = ((
                                            value / record.contract_id.resource_calendar_id.monthly_hours) * record.factor) * record.quantity
                    record.ns_value = ((
                                               ns_value / record.contract_id.resource_calendar_id.monthly_hours) * record.factor) * record.quantity
                record.s_value = record.value
                record.total_compensated = record.ns_value + record.s_value

            else:
                value = record.contract_id.food_aid if record.novelty_type_id.take_ns else record.contract_id.wage
                if record.novelty_type_id.self_calculating:
                    if record.type_calculation == 'days':
                        record.value = (value / 30) * record.quantity
                    elif record.type_calculation == 'hours':
                        record.value = ((value / record.contract_id.resource_calendar_id.monthly_hours) *
                                        record.quantity)
                if record.novelty_type_id.apply_factor:
                    record.value = ((
                                            value / record.contract_id.resource_calendar_id.monthly_hours) * record.factor) * record.quantity

    def action_approval(self):
        novelty_type = self.env['hr.novelty.type'].search([('is_ns_vacation_compensated', '=', True)], limit=1)
        for record in self:
            if record.novelty_type_id.is_vacation_compensated and record.ns_value > 0:
                novelty = record.env['hr.novelty'].create({
                    'novelty_type_id': novelty_type.id,
                    'employee_id': record.employee_id.id,
                    'contract_id': record.contract_id.id,
                    'date_start': record.date_start,
                    'company_id': record.company_id.id,
                    'quantity': record.quantity,
                    'value': record.ns_value,
                })
                novelty.action_pending_approval()
                novelty.action_approval()
                record.novelty_id = novelty.id
            record.write({'state': 'approval'})

    @api.model
    def create(self, vals):
        res = super(HrNovelty, self).create(vals)
        if res.value == 0.0:
            raise UserError(_("It is not possible to create a novelty with value 0"))
        return res
