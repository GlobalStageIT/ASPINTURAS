from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.addons.hr_payroll_custom.utils import days360


class HrVacation(models.Model):
    _name = 'hr.vacation'
    _description = "Hr Vacation"

    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee")
    identification = fields.Char(related='employee_id.identification_id', string="Identification")
    contract_id = fields.Many2one(comodel_name='hr.contract', string="Contract")
    company_id = fields.Many2one(comodel_name='res.company', string="Company")
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    wage = fields.Monetary(related='contract_id.wage', string="Wage")
    date_start = fields.Date(string="Date Start")
    worked_days = fields.Float(string="Worked Days")
    provisioned = fields.Float(string="Provisioned")
    taken = fields.Float(compute="_compute_taken", string="Taken", store=True)
    balance = fields.Float(compute="_value_balance", string="Balance")
    to_paid = fields.Float(compute="_value_to_paid", string="To Paid")
    leave_allocation_id = fields.Many2one('hr.leave.allocation', string="Leave Allocation ID")
    validation_note = fields.Char(string="Validation note")
    contract_date_end = fields.Date(related='contract_id.date_end', store=True, readonly=True)
    contract_status = fields.Selection(string='Estado del Contrato', related='contract_id.state', store=True, readonly=True)

    def _compute_taken(self):
        for vacation in self:
            leave_records = self.env['hr.leave'].search([
                ('employee_id', '=', vacation.employee_id.id),
                ('contract_id', '=', vacation.contract_id.id),
                ('holiday_status_id.is_vacation', '=', True),
                ('state', '=', 'validate')
            ])
            novelty_records = self.env['hr.novelty'].search([
                ('employee_id', '=', vacation.employee_id.id),
                ('contract_id', '=', vacation.contract_id.id),
                ('novelty_type_id.is_vacation_compensated', '=', True),
                ('state', '=', 'approval')
            ])

            total_taken = sum(abs(leave.number_of_days) for leave in leave_records)
            total_taken += sum(novelty.quantity for novelty in novelty_records)
            vacation.taken = total_taken

    def _value_balance(self):
        for record in self:
            record.balance = record.provisioned - record.taken

    def _value_to_paid(self):
        for record in self:
            record.to_paid = record.contract_id.wage / 30 * record.balance

    @api.model
    def _auto_provisioned_vacation(self):
        """
        Acción planificada diaria:
        1. Crear provisiones de vacaciones en contratos activos sin registro en hr_vacation.
        2. Actualizar balances (worked_days y provisioned) en registros existentes.
        """

        today = fields.Date.today()

        # --- 1. Buscar contratos sin provisión ---
        self.env.cr.execute("""
                    SELECT c.id, c.date_start, c.employee_id, c.company_id
                    FROM hr_contract c
                    JOIN hr_employee e ON c.employee_id = e.id
                    WHERE c.active = TRUE
                      AND e.employee_type = 'employee'
                      AND c.date_start <= CURRENT_DATE
                      AND NOT EXISTS (
                          SELECT 1 FROM hr_vacation v WHERE v.contract_id = c.id
                      );
                """)
        missing_contracts = self.env.cr.fetchall()  # [(id, date_start, employee_id, company_id), ...]

        holiday_status_id = self.env['hr.leave.type'].search([('is_vacation', '=', True)], limit=1)

        leave_vals, vacation_vals = [], []
        for contract_id, date_start, employee_id, company_id in missing_contracts:
            worked_days = days360(date_start, today) + 1
            provisioned = (worked_days / 30) * 1.25

            leave_vals.append({
                'name': _("Vacation Provisioned"),
                'holiday_status_id': holiday_status_id.id,
                'allocation_type': 'regular',
                'date_from': date_start,
                'employee_id': employee_id,
                'contract_id': contract_id,
                'number_of_days': provisioned,
                'is_provisioned_vacation': True,
            })
            vacation_vals.append({
                'employee_id': employee_id,
                'contract_id': contract_id,
                'company_id': company_id,
                'date_start': date_start,
                'worked_days': worked_days,
                'provisioned': provisioned,
            })

        # Bulk create para mayor velocidad
        allocations = self.env['hr.leave.allocation'].create(leave_vals)
        for vac_val, alloc in zip(vacation_vals, allocations):
            vac_val['leave_allocation_id'] = alloc.id
        self.create(vacation_vals)

        # --- 2. Actualizar balances de TODOS los contratos con provisión ---
        vacations = self.search([('date_start', '<=', today), '|',('contract_id.date_end', '!=', False), ('contract_id.date_end', '<=', today)])  # o limitar a activos
        for record in vacations:
            if not record.contract_id:
                continue

            contract = record.contract_id
            termination_date, liquidation = None, False

            # fecha de liquidación si aplica
            if contract.date_end:
                termination_date = contract.date_end
                liquidation = True
            else:
                termination_date = today

            # días no justificados
            self.env.cr.execute("""
                        SELECT COALESCE(SUM(amount), 0)
                        FROM hr_payslip_line
                        WHERE contract_id = %s
                          AND code IN ('DIAS_LIC_NO_REM', 'DIAS_AUSEN_NO_JUST', 'DIA_DESC_DOMINICAL')
                          AND slip_id IN (
                              SELECT id FROM hr_payslip WHERE state = 'done'
                          )
                    """, (contract.id,))
            days_no_just = self.env.cr.fetchone()[0] or 0

            # cálculo de días trabajados
            worked_days = (days360(contract.date_start, termination_date) + 1) - days_no_just
            provisioned = (worked_days / 30) * 1.25 if worked_days > 0 else (1 / 30) * 1.25

            # si es liquidación, cerrar allocation
            if liquidation:
                record.leave_allocation_id.write({
                    'date_to': termination_date,
                    'state': 'refuse',
                })

            # actualizar vacation y allocation
            record.write({
                'worked_days': worked_days,
                'provisioned': provisioned,
            })

            record.leave_allocation_id.with_context(vacation=record).write({
                'leaves_taken': record.taken,
                'number_of_days': provisioned,
                'number_of_days_display': provisioned,
            })