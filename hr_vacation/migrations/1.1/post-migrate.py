import logging

from odoo import api, fields, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Asignaciones sin empleados en employee_ids: al recalcularse employee_id
    # queda en NULL y viola hr_leave_allocation_type_value.
    cr.execute("""
        INSERT INTO hr_employee_hr_leave_allocation_rel (hr_leave_allocation_id, hr_employee_id)
        SELECT a.id, a.employee_id
          FROM hr_leave_allocation a
         WHERE a.holiday_type = 'employee'
           AND a.employee_id IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM hr_employee_hr_leave_allocation_rel r
                            WHERE r.hr_leave_allocation_id = a.id)
    """)
    _logger.info("hr_vacation: %s asignaciones con employee_ids reparado", cr.rowcount)

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
