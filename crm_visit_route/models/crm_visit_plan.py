# -*- coding: utf-8 -*-
from datetime import datetime, date, time
import calendar
from odoo import api, fields, models, _

class CrmVisitPlan(models.Model):
    _name = "crm.visit.plan"
    _description = "Plantilla de visitas"
    _order = "name"

    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", string="Asesor", required=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many("crm.visit.plan.line", "plan_id", string="Líneas")

    def action_generate_today(self):
        today = fields.Date.context_today(self)
        for plan in self:
            plan._generate_visits_for_date(today)

    def _generate_visits_for_date(self, for_date=None):
        if for_date is None:
            for_date = fields.Date.context_today(self)
        if isinstance(for_date, str):
            for_date = fields.Date.from_string(for_date)

        Visit = self.env["crm.visit"]
        for plan in self:
            for line in plan.line_ids:
                if not line._matches_date(for_date):
                    continue
                hour_int = int(line.hour)
                minute = int(round((line.hour - hour_int) * 60.0))
                dt_start = datetime.combine(
                    for_date, time(hour=hour_int, minute=minute)
                )
                existing = Visit.search(
                    [
                        ("partner_id", "=", line.partner_id.id),
                        ("user_id", "=", plan.user_id.id),
                        ("scheduled_date", ">=", fields.Datetime.to_string(dt_start)),
                        ("scheduled_date", "<=", fields.Datetime.to_string(dt_start)),
                    ],
                    limit=1,
                )
                if existing:
                    continue
                Visit.create(
                    {
                        "name": line.name or _("Visita %s") % line.partner_id.display_name,
                        "partner_id": line.partner_id.id,
                        "user_id": plan.user_id.id,
                        "scheduled_date": fields.Datetime.to_string(dt_start),
                        "duration_minutes": line.duration_minutes or 30,
                        "zone_id": line.zone_id.id,
                        "priority": line.priority,
                    }
                )

class CrmVisitPlanLine(models.Model):
    _name = "crm.visit.plan.line"
    _description = "Línea de plantilla de visitas"
    _order = "weekday, hour, id"

    name = fields.Char(string="Descripción")
    plan_id = fields.Many2one("crm.visit.plan", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    zone_id = fields.Many2one("crm.visit.zone", string="Zona")
    weekday = fields.Selection(
        [
            ("0", "Lunes"),
            ("1", "Martes"),
            ("2", "Miércoles"),
            ("3", "Jueves"),
            ("4", "Viernes"),
            ("5", "Sábado"),
            ("6", "Domingo"),
        ],
        string="Día semana",
        required=True,
    )
    hour = fields.Float(
        string="Hora",
        help="Hora del día (por ejemplo 9.5 = 09:30).",
        required=True,
        default=9.0,
    )
    duration_minutes = fields.Integer(
        string="Duración (min)", default=30,
    )
    priority = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta")],
        default="1",
        string="Prioridad",
    )

    interval_unit = fields.Selection(
        [
            ("none", "Sin intervalo"),
            ("days", "Cada N días"),
            ("weeks", "Cada N semanas"),
            ("months", "Cada N meses"),
        ],
        default="none",
        string="Unidad intervalo",
    )
    interval_number = fields.Integer(
        default=1,
        string="Cada",
    )
    start_date = fields.Date(
        string="Fecha inicio intervalo",
        help="Si se define, se usará como referencia para la repetición.",
    )

    def _matches_date(self, for_date):
        self.ensure_one()
        if isinstance(for_date, str):
            for_date = fields.Date.from_string(for_date)
        if self.weekday and int(self.weekday) != for_date.weekday():
            return False
        if self.interval_unit == "none":
            return True
        if not self.start_date:
            return False
        sd = self.start_date
        if self.interval_number <= 0:
            return False

        if self.interval_unit == "days":
            delta = (for_date - sd).days
            return delta >= 0 and (delta % self.interval_number) == 0
        if self.interval_unit == "weeks":
            delta = (for_date - sd).days
            return delta >= 0 and ((delta // 7) % self.interval_number) == 0
        if self.interval_unit == "months":
            if for_date < sd:
                return False
            months = (for_date.year - sd.year) * 12 + (for_date.month - sd.month)
            last_dom = calendar.monthrange(for_date.year, for_date.month)[1]
            same_dom = for_date.day == sd.day
            flex_dom_ok = sd.day > last_dom and for_date.day == last_dom
            return (months % self.interval_number == 0) and (same_dom or flex_dom_ok)
        return False
