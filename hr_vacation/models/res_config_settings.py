from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    type_contracts_provision = fields.Many2many(related='company_id.type_contracts_provision', readonly=False)
    type_leave_vacation = fields.Many2one(related='company_id.type_leave_vacation', readonly=False)
    type_novelty_vacation = fields.Many2one(related='company_id.type_novelty_vacation', readonly=False)

    @api.constrains('type_novelty_vacation')
    def default_type_novelty(self):
        type_novelty_vacation = self.type_novelty_vacation
        type_novelty_vacation.is_vacation_compensated = True
        self.env['hr.novelty.type'].search(
            [('id', '!=', type_novelty_vacation.id), ('is_vacation_compensated', '=', True)]).write(
            {'is_vacation_compensated': False})
