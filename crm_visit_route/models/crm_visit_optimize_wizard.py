# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmVisitOptimizeWizard(models.TransientModel):
    _name = "crm.visit.optimize.wizard"
    _description = "Optimizar ruta (selección)"

    visit_ids = fields.Many2many("crm.visit", string="Visitas a optimizar")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "crm.visit":
            res["visit_ids"] = [
                (6, 0, self.env.context.get("active_ids", []))
            ]
        return res

    def action_optimize(self):
        self.ensure_one()
        if not self.visit_ids:
            raise UserError(_("No hay visitas seleccionadas."))

        visits = self.visit_ids.sorted(
            key=lambda r: r.scheduled_date or fields.Datetime.now()
        )
        url = visits[0]._maps_url_for_visits(visits)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
