from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    novelty_ids = fields.One2many('hr.novelty', 'payslip_id', string="Novelty's")

    def get_qty_earn(self, code: str) -> int:
        value = 0
        if self.novelty_ids:
            value = sum(self.novelty_ids.filtered(lambda l: l.type == 'income').mapped('quantity'))
        return value

    def get_qty_deduction(self, code: str) -> int:
        value = 0
        if self.novelty_ids:
            value = sum(self.novelty_ids.filtered(lambda l: l.type == 'deduction').mapped('quantity'))
        return value

    def action_compute_sheet(self):
        for payslip in self:
            """
            
                Buscar novedades en las fechas configuradas de en el periodo
            
            """
            date_start = payslip.payroll_period_id.novelty_date_start
            date_to = payslip.payroll_period_id.date_end if payslip.is_settlement else payslip.payroll_period_id.novelty_date_end

            noveltys_not_date_end = payslip.env['hr.novelty'].search([
                ('contract_id', '=', payslip.contract_id.id), ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'approval'), ('date_start', '>=', date_start), ('date_start', '<=', date_to)
            ])

            noveltys_date_end = payslip.env['hr.novelty'].search([
                ('contract_id', '=', payslip.contract_id.id), ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'approval'),
                ('date_start', '<=', date_to), ('date_end', '!=', False),
                ('date_end', '>=', date_start)
            ])

            """ Agregar novedades en las en la nómina """
            novelties = noveltys_not_date_end + noveltys_date_end
            payslip.novelty_ids = [(6, 0, novelties.ids)]

            """
            
                Homologar novedades a entradas de nómina hr.payslip.input
            
            """

            input_line_list = []
            for input_line in payslip.input_line_ids:
                payslip.input_line_ids = [(2, input_line.id)]
            for novelty in payslip.novelty_ids:

                input_line_list.append((0, 0, {
                    'name': novelty.novelty_type_id.name,
                    'payslip_id': payslip.id,
                    'code': novelty.code,
                    'amount': novelty.value,
                    'contract_id': payslip.contract_id.id,
                    'novelty_id': novelty.id,
                }))

            # Add lines
            payslip.update({'input_line_ids': input_line_list})

        return super(HrPayslip, self).action_compute_sheet()
