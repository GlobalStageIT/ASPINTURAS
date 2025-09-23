from odoo import models, fields

class EntityType(models.Model):
    _name = "entity.type"
    _description = "Tipo de Entidad"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Selection(
        selection=[
            ('eps', 'EPS'),
            ('arl', 'ARL'),
            ('cesantias', 'Cesantías'),
            ('pension', 'Fondo de Pensiones'),
            ('caja', 'Caja de Compensación'),
        ],
        string='Código',
        required=True
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    entity_type_ids = fields.Many2many(
        'entity.type',
        'partner_entity_rel',
        'partner_id',
        'entity_id',
        string="Tipos de Entidad"
    )
