from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrNovelty(models.Model):
    _name = 'hr.novelty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Novelty of Payroll'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    name = fields.Char(string='Number', copy=False, readonly=True, required=True, default=lambda x: _('New'))
    code = fields.Char(related='novelty_type_id.code')
    novelty_type_id = fields.Many2one('hr.novelty.type', string='Novelty Type', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    wage = fields.Monetary(related='contract_id.wage')
    date_start = fields.Date(string='Date Start', required=True, default=fields.Date.today(), tracking=True)
    date_end = fields.Date(string='Date End', tracking=True)
    quantity = fields.Float(string='Quantity', tracking=True)
    value = fields.Float(string='Value', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approval', 'Approved'),
        ('rejected', 'Refused'),
    ], string='State', default='draft', required=True, tracking=True)
    identification = fields.Char(string='Identification')

    type = fields.Selection(related='novelty_type_id.type')
    factor = fields.Float(related='novelty_type_id.factor')
    type_calculation = fields.Selection(related='novelty_type_id.type_calculation')
    apply_date_end = fields.Boolean(related='novelty_type_id.apply_date_end')
    apply_factor = fields.Boolean(related='novelty_type_id.apply_factor')
    apply_quantity = fields.Boolean(related='novelty_type_id.apply_quantity')
    formula = fields.Html(related='novelty_type_id.formula')

    ''' Cambios de estados '''

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_pending_approval(self):
        self.write({'state': 'pending_approval'})

    def action_approval(self):
        self.write({'state': 'approval'})

    def action_rejected(self):
        self.write({'state': 'rejected'})

    @api.constrains('quantity')
    @api.onchange('quantity')
    def self_calculating(self):
        """ Calculo de la novedad cuando es tipo cantidad """
        for record in self:
            value = record.contract_id.wage
            if record.self_calculating:
                if record.type_calculation == 'days':
                    record.value = (value / 30) * record.quantity
                elif record.type_calculation == 'hours':
                    record.value = ((value / record.contract_id.resource_calendar_id.monthly_hours) *
                                    record.quantity)
            if record.apply_factor:
                record.value = ((
                                        value / record.contract_id.resource_calendar_id.monthly_hours) * record.factor) * record.quantity

    @api.onchange('novelty_type_id')
    def calculated_quantity(self):
        """ Si aplica cantidad valida """
        for record in self:
            if not record.apply_quantity:
                record.quantity = 1
            else:
                record.quantity = 0
            record.value = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            if vals['value'] == 0.0:
                raise UserError(_("It is not possible to create a novelty with value 0"))

            # Validación para el cargue masivo por identificación
            if vals.get('identification'):
                employee_id = self.env['hr.employee'].search([('identification_id', '=', vals.get('identification'))])
                if not employee_id:
                    raise UserError(
                        _("No valid employee was found for the identification %s." % vals.get('identification')))
                else:
                    vals['employee_id'] = employee_id.id
                contract_id = self.env['hr.contract'].search([('employee_id', '=', employee_id.id), ('state', '=', 'open')])
                if not contract_id:
                    raise UserError(_("No valid contract was found for the employee %s." % employee_id.name))
                else:
                    vals['contract_id'] = contract_id.id
                if not contract_id.company_id:
                    raise UserError(_("No valid company was found for the employee %s." % employee_id.name))
                else:
                    vals['company_id'] = contract_id.company_id.id

            # Secuencia
            vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code('hr.novelty')

        return super(HrNovelty, self).create(vals_list)
