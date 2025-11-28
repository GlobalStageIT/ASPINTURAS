# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmVisit(models.Model):
    _name = "crm.visit"
    _description = "Visita a cliente"
    _order = "priority desc, scheduled_date asc, id asc"

    name = fields.Char(required=True, default="Visita")
    partner_id = fields.Many2one("res.partner", required=True, string="Cliente")
    user_id = fields.Many2one(
        "res.users",
        string="Asesor",
        default=lambda self: self.env.user,
        required=True,
    )
    scheduled_date = fields.Datetime(required=True, string="Inicio programado")
    scheduled_date_end = fields.Datetime(
        string="Fin programado",
        compute="_compute_scheduled_end",
        store=True,
    )
    duration_minutes = fields.Integer(
        default=30,
        string="Duración (min)",
        help="Duración planeada de la visita.",
    )

    state = fields.Selection(
        [
            ("scheduled", "Programada"),
            ("in_progress", "En curso"),
            ("done", "Finalizada"),
            ("cancelled", "Cancelada"),
        ],
        default="scheduled",
        string="Estado",
        tracking=True,
    )

    priority = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta")],
        default="1",
        index=True,
        string="Prioridad",
    )
    zone_id = fields.Many2one("crm.visit.zone", string="Zona")

    sale_order_id = fields.Many2one("sale.order", string="Pedido/Cotización")

    checkin_time = fields.Datetime(string="Inicio real")
    checkin_lat = fields.Float(string="Latitud check-in")
    checkin_lng = fields.Float(string="Longitud check-in")

    checkout_time = fields.Datetime(string="Fin real")
    checkout_lat = fields.Float(string="Latitud check-out")
    checkout_lng = fields.Float(string="Longitud check-out")

    @api.depends("scheduled_date", "duration_minutes")
    def _compute_scheduled_end(self):
        for visit in self:
            if visit.scheduled_date:
                duration = visit.duration_minutes or 30
                visit.scheduled_date_end = visit.scheduled_date + timedelta(
                    minutes=duration
                )
            else:
                visit.scheduled_date_end = False

    def _get_travel_mode(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("crm_visit_route.travel_mode")
        )
        return param or "driving"

    def _maps_url_for_visits(self, visits):
        self.ensure_one()
        import urllib.parse

        if not visits:
            raise UserError(_("No hay visitas para construir la ruta."))

        addrs = []
        for v in visits:
            addr = v.partner_id.contact_address or v.partner_id.display_name
            if addr:
                addrs.append(addr)

        if not addrs:
            raise UserError(_("No hay direcciones para construir la ruta."))

        base = "https://www.google.com/maps/dir/?api=1"
        mode = self._get_travel_mode()

        if len(addrs) == 1:
            dest = urllib.parse.quote_plus(addrs[0])
            return f"{base}&destination={dest}&travelmode={mode}"

        waypoints = "|".join(addrs[:-1])
        dest = urllib.parse.quote_plus(addrs[-1])
        wp = urllib.parse.quote_plus(waypoints)
        return (
            f"{base}&origin=Current+Location&destination={dest}"
            f"&waypoints={wp}&travelmode={mode}"
        )

    def action_open_maps_single(self):
        self.ensure_one()
        url = self._maps_url_for_visits(self)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def _visits_for_day(self, the_date, user):
        start = datetime.combine(the_date, datetime.min.time())
        end = datetime.combine(the_date, datetime.max.time())
        return self.search(
            [
                ("user_id", "=", user.id),
                ("scheduled_date", ">=", fields.Datetime.to_string(start)),
                ("scheduled_date", "<=", fields.Datetime.to_string(end)),
            ],
            order="scheduled_date asc, id asc",
        )

    @api.model
    def _action_open_maps_for_today_current_user(self):
        user = self.env.user
        today = fields.Date.context_today(self)
        visits = self._visits_for_day(today, user)
        if not visits:
            raise UserError(_("No hay visitas para hoy."))
        url = visits[:1]._maps_url_for_visits(visits)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def action_geocheck(self, lat, lng):
        """Registrar check-in / check-out (primera vez check-in, segunda check-out)."""
        now = fields.Datetime.now()
        for visit in self:
            vals = {}
            if not visit.checkin_time:
                vals.update(
                    {
                        "checkin_time": now,
                        "checkin_lat": lat,
                        "checkin_lng": lng,
                        "state": "in_progress",
                    }
                )
            else:
                vals.update(
                    {
                        "checkout_time": now,
                        "checkout_lat": lat,
                        "checkout_lng": lng,
                        "state": "done",
                    }
                )
            visit.write(vals)
        return True

    def action_create_quotation(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("La visita no tiene cliente asignado."))

        SaleOrder = self.env["sale.order"]
        order = SaleOrder.create(
            {
                "partner_id": self.partner_id.id,
                "user_id": self.user_id.id,
                "origin": f"Visit {self.name}",
            }
        )
        self.sale_order_id = order.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "views": [
                (self.env.ref("crm_visit_route.view_sale_order_crm_visit_form").id, "form")
            ],
            "res_id": order.id,
        }

    def action_open_calendar(self):
        action = self.env.ref("crm_visit_route.action_crm_visit").read()[0]
        action["view_mode"] = "calendar,tree,form"
        return action
