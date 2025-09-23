from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    state = fields.Selection(
        [('new', 'Nuevo 🟢'), ('process', 'En proceso 🟢'), ('retiring', 'En proceso de retiro 🟡'), ('retired', 'Retirado 🟠')], string="Estado")
    eps = fields.Many2one('res.partner', string='EPS', tracking=True)
    arl = fields.Many2one('res.partner', string='ARL', tracking=True)
    ccf = fields.Many2one('res.partner', string='CCF', tracking=True)
    layoffs = fields.Many2one('res.partner', string='Layoffs', tracking=True)
    pension = fields.Many2one('res.partner', string='Pension', tracking=True)
    arl_risk_id = fields.Many2one('hr.employee.arl.risk', string='Risk Level')
    arl_contribution_percentage = fields.Float('Contribution %', related='arl_risk_id.contribution_percentage')
    professional_card = fields.Selection([
        ('si', 'Si'),
        ('no', 'No')
    ], string='¿Tarjeta Profesional?')
    card_number = fields.Char(string='Número de Tarjeta')
    issue_date = fields.Date(string='Fecha de Expedición')
    card_attachment = fields.Binary(string='Adjuntar Tarjeta')
    card_filename = fields.Char(string='Nombre del Archivo')
    competencies = fields.Text(string='Competencias')
    show_card_fields = fields.Boolean(string="Mostrar campos de tarjeta", compute='_compute_show_card_fields',
                                      store=False)
    #Contract fields

    contract_department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Departamento",
        related="contract_id.department_id",
        store=False
    )

    contract_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Cuenta Analítica",
        related="contract_id.analytic_account_id",
        store=True
    )

    contract_type_id = fields.Many2one(
        comodel_name="hr.contract.type",
        string="Tipo de Contrato",
        related="contract_id.contract_type_id",
        store=True
    )

    contract_state = fields.Selection(
        string="Estado Contrato",
        related="contract_id.state",
        store=False
    )

    contract_start_date = fields.Date(
        string="Inicio Contrato",
        related="contract_id.date_start",
        store=False
    )
    contract_end_date = fields.Date(
        string="Fin Contrato",
        related="contract_id.date_end",
        store=False
    )

    contract_wage = fields.Monetary(
        string="Salario",
        related="contract_id.wage",
        store=False
    )

    @api.depends('professional_card')
    def _compute_show_card_fields(self):
        for record in self:
            record.show_card_fields = record.professional_card == 'si'
