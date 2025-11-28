# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class CrmVisitApi(http.Controller):

    @http.route("/api/visits/today", type="json", auth="user", methods=["POST"])
    def visits_today(self, **kwargs):
        """Devolver visitas del usuario logueado para hoy."""
        user = request.env.user
        Visit = request.env["crm.visit"]
        today = request.env["ir.fields.converter"]._today(request.env)
        domain = [
            ("user_id", "=", user.id),
            ("scheduled_date", ">=", today + " 00:00:00"),
            ("scheduled_date", "<=", today + " 23:59:59"),
        ]
        recs = Visit.search(domain, order="scheduled_date asc, id asc")

        def _coords(v):
            return {
                "checkin_lat": v.checkin_lat,
                "checkin_lng": v.checkin_lng,
                "checkout_lat": v.checkout_lat,
                "checkout_lng": v.checkout_lng,
            }

        return [
            {
                "id": v.id,
                "name": v.name,
                "partner_id": v.partner_id.id,
                "partner_name": v.partner_id.display_name,
                "scheduled_date": v.scheduled_date,
                "scheduled_date_end": v.scheduled_date_end,
                "state": v.state,
                **_coords(v),
            }
            for v in recs
        ]

    @http.route("/api/visits/<int:visit_id>/checkin", type="json", auth="user", methods=["POST"])
    def visit_checkin(self, visit_id, lat=None, lng=None, **kw):
        """Registrar check-in / check-out usando la misma lógica del botón."""
        if lat is None or lng is None:
            return {"ok": False, "error": "Missing coordinates."}
        Visit = request.env["crm.visit"]
        visit = Visit.browse(visit_id)
        if not visit.exists():
            return {"ok": False, "error": "Visit not found."}
        visit.action_geocheck(float(lat), float(lng))
        return {"ok": True}

    @http.route("/api/visits/<int:visit_id>/maps", type="json", auth="user", methods=["POST"])
    def visit_maps_url(self, visit_id, **kw):
        Visit = request.env["crm.visit"]
        visit = Visit.browse(visit_id)
        if not visit.exists():
            return {"ok": False, "error": "Visit not found."}
        url = visit._maps_url_for_visits(visit)
        return {"url": url}
