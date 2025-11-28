# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.ui.view"].sudo().search([
        ("arch_db", "ilike", "ocapi_bindings")
    ]).write({"active": False})
