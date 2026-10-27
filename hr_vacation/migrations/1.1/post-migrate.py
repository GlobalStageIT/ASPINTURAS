import logging

from odoo import api, fields, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Libros de contratos terminados: se crearon contando días hasta la fecha
    # de creación y no hasta el fin del contrato, y la acción planificada ya
    # no los actualiza.
    env = api.Environment(cr, SUPERUSER_ID, {})
    today = fields.Date.today()
    vacations = env['hr.vacation'].search([
        ('contract_id.date_end', '!=', False),
        ('contract_id.date_end', '<', today),
    ])
    for vacation in vacations:
        try:
            with cr.savepoint():
                vacation._update_provisioned(today)
        except Exception as e:
            _logger.warning("hr_vacation: no se pudo recalcular el libro %s (%s): %s",
                            vacation.id, vacation.employee_id.name, e)
