# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crm_visit_route_travel_mode = fields.Selection(
        [
            ("driving", "Auto"),
            ("walking", "A pie"),
            ("bicycling", "Bicicleta"),
            ("transit", "Transporte público"),
        ],
        string="Modo de viaje (CRM Visitas)",
        config_parameter="crm_visit_route.travel_mode",
        default="driving",
    )
