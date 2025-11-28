# -*- coding: utf-8 -*-
from odoo import fields, models

class CrmVisitZone(models.Model):
    _name = "crm.visit.zone"
    _description = "Zona de visitas"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer()
    active = fields.Boolean(default=True)
