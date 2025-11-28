from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    monthly_hours = fields.Float(string="Monthly Hours", default=230)
