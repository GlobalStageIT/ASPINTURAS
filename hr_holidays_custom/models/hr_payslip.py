from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.hr_payroll_custom.utils import days360


def group_dates_by_week(dates):
    week_groups = {}
    for day in dates:
        monday = day - relativedelta(days=day.weekday())
        sunday = monday + relativedelta(days=6)

        week_number = day.isocalendar()[1]  # Get ISO week number
        if week_number not in week_groups and monday.month == sunday.month:
            week_groups[week_number] = []
            week_groups[week_number].append(day)

    return len(week_groups)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contracts: Browse record of contracts, date_from, date_to
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = self.payroll_period_id.novelty_date_start
            day_to = self.payroll_period_id.date_end if self.is_liquidation else self.payroll_period_id.novelty_date_end
            calendar = contract.resource_calendar_id

            leaves = {}
            leaves_employee = self.env['hr.leave'].search([
                ('employee_id', '=', contract.employee_id.id),
                ('contract_id', '=', contract.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', day_to),
                ('request_date_to', '>=', day_from),
            ])

            list_dates = []
            for leave in leaves_employee:
                date_start = day_from if day_from > leave.request_date_from < day_to else leave.request_date_from
                date_end = day_to if leave.request_date_to > day_to else leave.request_date_to
                number_of_days = self._get_number_of_days(date_start, date_end, calendar,
                                                          leave.holiday_status_id.take_worked_days)

                current_leave_struct = leaves.setdefault(leave.holiday_status_id, {
                    'name': leave.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': leave.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                    'leave_ids': [(4, leave.id)],
                })
                current_leave_struct['number_of_days'] += number_of_days
                current_leave_struct['number_of_hours'] += number_of_days * calendar.hours_per_day

                # Total days to dominical
                if leave.holiday_status_id.apply_dominican_discount:
                    leave_dates = [date_start + timedelta(days=day) for day in range(days360(date_start, date_end) + 1)]
                    list_dates += [day for day in leave_dates if day not in list_dates]

            # Rest days of all leaves
            leave_days = sum(item['number_of_days'] for item in leaves.values() if 'number_of_days' in item)
            worked_days = days360(date_from, date_to + relativedelta(days=1))

            if contract.date_start > date_from:
                days_income = contract.date_start.day - 1
                leave_days += days_income
                income = {
                    'name': _("Days of income"),
                    'sequence': 2,
                    'code': 'DIA_DE_INGRESO',
                    'number_of_days': days_income,
                    'number_of_hours': days_income * contract.resource_calendar_id.hours_per_day,
                    'contract_id': contract.id,
                }
                res.append(income)

            if self.env.context.get('date_liquidation') or self.date_liquidation:
                date_end = self.env.context.get('date_liquidation') or self.date_liquidation
                if date_end and date_end != date_to:
                    days_retirement = days360(date_end, date_to)
                    if days_retirement > 0:

                        dayofweek_str_list = list(
                            set(contract.employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek')))
                        dayofweek_int_list = [int(day) for day in dayofweek_str_list]

                        if date_end.weekday() == max(dayofweek_int_list):
                            days = 7 - (max(dayofweek_int_list) + 1)
                            days = min(days_retirement, days)
                            days_retirement -= days
                            attendances = {
                                'name': _("Days Not Worked Compensated"),
                                'sequence': 1,
                                'code': 'N_WORK_C',
                                'number_of_days': days,
                                'number_of_hours': days * contract.resource_calendar_id.hours_per_day,
                                'contract_id': contract.id,
                            }
                            leave_days += days
                            res.append(attendances)

                        leave_days += days_retirement
                        retirement = {
                            'name': _("Days of retirement"),
                            'sequence': 3,
                            'code': 'DIA_DE_RETIRO',
                            'number_of_days': days_retirement,
                            'number_of_hours': days_retirement * contract.resource_calendar_id.hours_per_day,
                            'contract_id': contract.id,
                        }
                        res.append(retirement)

            worked_days = worked_days - leave_days
            dominical_days = 0
            if list_dates:
                dominical_days = group_dates_by_week(list_dates)

            is_liquidation = self.is_liquidation
            if (is_liquidation or worked_days > 0) and dominical_days > 0:

                if worked_days < dominical_days and not is_liquidation:
                    dominical_days = worked_days

                if dominical_days > 0:
                    dominical = {
                        'name': _("Discount Dominical Days"),
                        'sequence': 2,
                        'code': 'DIA_DESC_DOMINICAL',
                        'number_of_days': dominical_days,
                        'number_of_hours': dominical_days * contract.resource_calendar_id.hours_per_day,
                        'contract_id': contract.id,
                    }
                    res.append(dominical)
                    worked_days -= dominical_days

            attendances = {
                'name': _("Worked Days"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': worked_days if worked_days > 0 or is_liquidation else 0,
                'number_of_hours': worked_days * contract.resource_calendar_id.hours_per_day,
                'contract_id': contract.id,
            }

            res.append(attendances)
            if bool(leaves):
                res.extend(leaves.values())
        return res

    def _get_number_of_days(self, date_from, date_to, calendar, take_worked_days=False):
        result = relativedelta(date_to, date_from).days + 1
        if take_worked_days:

            result = 0
            total_days = days360(date_from, date_to) + 1
            calendar_days = list(set(calendar.attendance_ids.mapped('dayofweek')))

            for day in range(total_days):
                date_init = date_from + timedelta(days=day)
                if str(date_init.weekday()) in calendar_days:
                    result += 1

            global_leaves = self.env['resource.calendar.leaves'].search(
                [('calendar_id', '=', False), ('date_from', '<=', date_to),
                 ('date_to', '>=', date_from)])

            for global_leave in global_leaves:
                if str(global_leave.date_from.weekday()) in calendar_days:
                    result -= 1

        return result

    def get_calculated_days(self, interval, code):
        result = 0

        day_from = self.payroll_period_id.novelty_date_start
        day_to = self.payroll_period_id.date_end if self.is_liquidation else self.payroll_period_id.novelty_date_end

        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('contract_id', '=', self.contract_id.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', day_to),
            ('request_date_to', '>=', day_from),
        ])

        for leave in leaves.filtered(lambda l: l.holiday_status_id.code == code):

            date_start = day_from if day_from > leave.request_date_from < day_to else leave.request_date_from
            date_end = day_to if leave.request_date_to > day_to else leave.request_date_to

            total_leave_days = [leave.request_date_from + relativedelta(days=days) for days in
                                range(days360(leave.request_date_from, leave.request_date_to) + 1)]

            leave_days = [date_start + relativedelta(days=days) for days in
                          range(days360(date_start, date_end) + 1)]

            for day in leave_days:
                if day in total_leave_days and interval[0] <= total_leave_days.index(day) + 1 <= interval[1]:
                    result += 1

        return result


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked.days'

    leave_ids = fields.One2many('hr.leave', 'payslip_worked_days_id', string='Leave')
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=False,
                                  help="The contract for which applied"
                                       "this input")
