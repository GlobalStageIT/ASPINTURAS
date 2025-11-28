from odoo import fields, models, _, api, tools
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import math
import babel
from ..utils import days360


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payroll_period_id = fields.Many2one('hr.payroll.period', string="Period", required=True)
    is_liquidation = fields.Boolean(string="Is Liquidation", default=False)
    date_liquidation = fields.Date(string="Liquidation Date")
    apply_compensation = fields.Boolean(string="Apply Compensation", default=False)
    pay_severance_interest = fields.Boolean(string='Pay Severance Interest')
    deduction_detail_ids = fields.Many2many(comodel_name='hr.payslip.line', relation='payslip_earn_detail_rel',
                                            string="Deductions Table")
    earn_detail_ids = fields.Many2many(comodel_name='hr.payslip.line', relation='payslip_deduction_detail_rel',
                                       string="Income Table")
    ret_html = fields.Html(string='Withholding Tax')

    def for_action_compute_sheet(self):
        for record in self:
            record.action_compute_sheet()

    def for_action_payslip_done(self):
        for record in self:
            record.action_payslip_done()

    def for_action_payslip_cancel(self):
        for record in self:
            record.action_payslip_cancel()

    def for_action_payslip_draft(self):
        for record in self:
            record.action_payslip_draft()

    def for_action_send_email(self):
        for record in self:
            record.action_send_email()

    def action_send_email(self):
        mail_template = self.env.ref('hr_payroll_custom.mail_template_payslip')
        for record in self:
            mail_template.send_mail(record.id, force_send=True)

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        """Function for getting Payslip Lines"""

        def _sum_salary_rule_category(localdict, category, amount):
            """Function for getting total sum of Salary Rule Category"""
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict['categories'].dict[category.code] \
                = category.code in localdict[
                'categories'].dict and localdict['categories'].dict[
                      category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            """Class for Browsable Object"""

            def __init__(self, employee_id, dict, env):
                """Function for getting employee_id,dict and env"""
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                """Function for return dict"""
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = 
                    pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date,
                                     code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip days with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, 
                    sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = 
                    pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date,
                                     code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip hours with respect to
                 from_date,to_date fields"""
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = 
                False then (pl.total) else (-pl.total) end)
                FROM hr_payslip as hp, hr_payslip_line as pl
                WHERE hp.employee_id = %s AND hp.state = 'done'
                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id 
                = pl.slip_id AND pl.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten
        # by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            payslip.input_line_ids = [(2, input_line.id)]
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs, 'self': self}
        # get the ids of the structures on the contracts and their
        # parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(
                set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in
                    # the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in
                                  rule._recursive_search_of_rules()]
        return list(result_dict.values())

    def action_compute_sheet(self):
        for record in self:
            record.ret_html = False
            record.onchange_employee()
        res = super(HrPayslip, self).action_compute_sheet()
        locale = self.env.context.get('lang') or 'en_US'

        """

            Correción de nóminas ya contabilizadas

        """

        for payslip in self:
            payslip.name = _('%s of %s for %s') % (
                _('Liquidation') if payslip.is_liquidation else _('Salary Slip'), payslip.employee_id.name, tools.ustr(
                babel.dates.format_date(date=payslip.date_from, format='MMMM-y', locale=locale)))

            previous_payslip = payslip.env['hr.payslip'].search(
                [('state', '=', 'done'), ('payroll_period_id', '=', payslip.payroll_period_id.id),
                 ('contract_id', '=', payslip.contract_id.id), ('employee_id', '=', payslip.employee_id.id)])

            deduction_detail_ids = []
            for deduction in payslip.line_ids.filtered(lambda l: l.type_concept == 'deduction'):
                deduction_detail_ids.append(deduction.id)
            payslip.deduction_detail_ids = [(6, 0, deduction_detail_ids)]

            earn_detail_ids = []
            for earn in payslip.line_ids.filtered(lambda l: l.type_concept == 'earn'):
                earn_detail_ids.append(earn.id)
            payslip.earn_detail_ids = [(6, 0, earn_detail_ids)]

            if previous_payslip:
                for payslip_line in previous_payslip.line_ids:

                    adjust_line = payslip.line_ids.filtered(
                        lambda l: l.code == payslip_line.code and round(l.total, 2) != round(payslip_line.total, 2))
                    if adjust_line:
                        if adjust_line.salary_rule_id.type_concept != 'other' and adjust_line.quantity > 1:
                            adjust_line.total = adjust_line.total - payslip_line.total
                            adjust_line.quantity = adjust_line.quantity - payslip_line.quantity
                        else:
                            adjust_line.amount = adjust_line.amount - payslip_line.amount
                            adjust_line.quantity = adjust_line.quantity
                    else:
                        delete_line = payslip.line_ids.filtered(
                            lambda l: l.code == payslip_line.code and round(l.total, 2) == round(payslip_line.total, 2))
                        if delete_line:
                            delete_line.unlink()
            payslip.compute_totals()
        return res

    def compute_ret_html(self, data):
        for rec in self:
            """ Genera el HTML con estructura de tabla para mejor presentación visual. """

            rec.ret_html = f"""
            <div style="width: 60%; margin: 20px auto; font-family: Arial, sans-serif;">
                <h3 style="color: #6A0DAD;">Cálculo Retención</h3>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="background-color: #6A0DAD; color: white;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Detalle Cálculos</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Ingresos Laborales</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('ingresos_laborales', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Aportes obligatorio de salud (4)%</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('aportes_salud', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Aportes obligatorio de pensión (4)%</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('aportes_pension', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Fondo de solidaridad pensional (1)%</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('fondo_solidaridad', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Ingresos No Constitutivos</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('total_ingresos_no_const', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Subtotal (1)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('subtotal_1', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Intereses de Vivivenda</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('pago_int_vivienda', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Medicina Prepagada</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('pagos_med_prepagada', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Dependientes Económicos</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('pagos_por_dependientes', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Deducciones Aplicables</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('total_deducciones', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Subtotal (2)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('subtotal_2', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Aportes Pensión Vol</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('aportes_pens_vol', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Aportes AFC</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('aportes_AFC', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Otras Rentas Exentas</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('otras_rentas_exentas', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Rentas Exentas</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('total_rentas_exentas', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Subtotal (3)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('subtotal_3', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd;">RENTA DE TRABAJO EXENTA MAX 25%</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('renta_trab_exenta_25', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Subtotal (4)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('subtotal_4', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Cifra Control 40%</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('cifra_control_40', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Deducciones Acumulables</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('deducciones_acum', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd;">Maximo Deducibles 111.66 UVT</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{data.get('max_deduc_uvt', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Min Deducible</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('min_deducible', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Ingreso Base</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('ing_base_refuente', 0.00):,.2f}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Ingreso Gravado UVT</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('ingreso_gravado_uvt', 0.00):,.2f}</td></tr>

                        <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">TOTAL</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{data.get('result', 0.00):,.2f}</td></tr>

                    </tbody>
                </table>
            </div>
            """

    @api.constrains('payroll_period_id', 'contract_id')
    def _value_dates(self):
        for record in self:
            if record.payroll_period_id:
                if record.contract_id.date_end and (record.contract_id.date_end < record.payroll_period_id.date_start):
                    raise UserError(_("It is not possible to execute payroll for the employee %s, the end date of the "
                                      "contract is less than the initial date of the payroll." % record.employee_id.name))

    @api.onchange('payroll_period_id')
    def calculated_dates(self):
        self.date_from = self.payroll_period_id.date_start
        self.date_to = self.payroll_period_id.date_end

    def action_payslip_done(self):
        if self.move_id:
            raise UserError(
                _('It is not possible to account for the payroll, since it has an associated accounting entry.'))

        def get_partner(line, input=None, is_debit=True):
            concept_type = line.salary_rule_id.type_concept
            if concept_type == 'deduction' and is_debit:
                return line._get_partner_id(credit_account=False, is_employee=True)
            elif concept_type == 'earn' and not is_debit:
                return line._get_partner_id(credit_account=True, is_employee=True)
            # elif input and input.loan_id:
            #     return input.loan_id.partner_id.id
            return line._get_partner_id(credit_account=not is_debit)

        for slip in self:
            line_ids, debit_sum, credit_sum = [], 0.0, 0.0
            move_dict = {
                'narration': _('Payslip of %s') % slip.employee_id.name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': slip.date or slip.date_to,
                'partner_id': slip.employee_id.work_contact_id.id,
            }

            for line in slip.line_ids:
                is_multiple = line.salary_rule_id.multiple_lines
                inputs = self.novelty_ids.filtered(lambda l: l.code == line.code) if is_multiple else [line]

                for input in inputs:
                    amount = slip.company_id.currency_id.round(
                        slip.credit_note and -getattr(input, 'value', 0.0) or getattr(input, 'value', line.total))
                    if slip.company_id.currency_id.is_zero(amount):
                        continue

                    sss = line.salary_rule_id.mapped('specific_struct_salary_ids').filtered(
                        lambda s: s.struct_id.id == slip.struct_id.id)
                    debit_account_id = sss.account_debit.id if sss else line.salary_rule_id.account_debit_id.id
                    credit_account_id = sss.account_credit.id if sss else line.salary_rule_id.account_credit_id.id

                    if debit_account_id:
                        debit = {
                            'name': line.name,
                            'partner_id': get_partner(line, input=input, is_debit=True),
                            'account_id': debit_account_id,
                            'journal_id': slip.journal_id.id,
                            'date': slip.date or slip.date_to,
                            'debit': max(amount, 0.0),
                            'credit': -min(amount, 0.0),
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                            'payroll_type_rule': line.salary_rule_id.payroll_type_rule,
                        }
                        line_ids.append((0, 0, debit))
                        debit_sum += debit['debit'] - debit['credit']

                    if credit_account_id:
                        credit = {
                            'name': line.name,
                            'partner_id': get_partner(line, input=input, is_debit=False),
                            'account_id': credit_account_id,
                            'journal_id': slip.journal_id.id,
                            'date': slip.date or slip.date_to,
                            'debit': -min(amount, 0.0),
                            'credit': max(amount, 0.0),
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                            'payroll_type_rule': line.salary_rule_id.payroll_type_rule,
                        }
                        line_ids.append((0, 0, credit))
                        credit_sum += credit['credit'] - credit['debit']

            # Ajuste si hay diferencia entre débitos y créditos
            difference = slip.company_id.currency_id.round(debit_sum - credit_sum)
            if not slip.company_id.currency_id.is_zero(difference):
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the %s Account!') % (
                        slip.journal_id.name, 'Credit' if difference > 0 else 'Debit'))

                adjust_line = {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': slip.date or slip.date_to,
                    'debit': 0.0 if difference > 0 else abs(difference),
                    'credit': abs(difference) if difference > 0 else 0.0,
                }
                line_ids.append((0, 0, adjust_line))

            # Agrupación de líneas por cuenta y partner si aplica
            grouped = []
            for line in line_ids:
                data = line[2]
                account = slip.env['account.account'].browse(data['account_id'])
                found = False
                for g in grouped:
                    gdata = g[2]
                    if (gdata['account_id'] == data['account_id'] and
                            gdata['partner_id'] == data['partner_id'] and
                            account.group_payslip and
                            slip.employee_id.work_contact_id.id == data['partner_id']):
                        gdata['credit'] += data['credit']
                        gdata['debit'] += data['debit']
                        gdata['name'] = _("SALARIOS POR PAGAR")
                        gdata['payroll_type_rule'] = 'payroll'
                        found = True
                        break
                if not found:
                    grouped.append(line)

            # Ajustar saldos agrupados si es necesario
            for line in grouped:
                data = line[2]
                account = slip.env['account.account'].browse(data['account_id'])
                if account.group_payslip:
                    if data['credit'] >= data['debit']:
                        data['credit'] -= data['debit']
                        data['debit'] = 0
                    else:
                        data['debit'] -= data['credit']
                        data['credit'] = 0
                        data['account_id'] = account.debit_account_payslip.id

            move_dict['line_ids'] = grouped
            move = slip.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': slip.date or slip.date_to, 'state': 'done'})

            if not move.line_ids:
                raise UserError(_(
                    "As you installed the payroll accounting module you have to choose "
                    "Debit and Credit account for at least one salary rule in the chosen Salary Structure."))

            move.action_post()

        return

    ''' Métodos Calculo de nómina '''

    def get_days(self, date_a, date_b, not_sum_1=False):
        res = days360(date_a, date_b) + 1
        if not_sum_1:
            res -= 1
        return res

    def get_days_worked_year(self, date_end):
        return days360(max(date_end + relativedelta(month=1, day=1), self.contract_id.date_start), date_end) + 1

    def get_days_worked_semiannual(self):
        date_end = self.date_liquidation
        if date_end.month > 6:
            date_start = max(self.contract_id.date_start, date_end + relativedelta(month=7, day=1))
        else:
            date_start = max(self.contract_id.date_start, date_end + relativedelta(month=1, day=1))
        return days360(date_start, date_end) + 1

    def get_history_values(self, code: str, historic_type: str, annual=False):
        date_from = self.date_from
        date_to = self.date_liquidation or self.date_to
        initial_year = self.date_from + relativedelta(month=1, day=1)

        if historic_type == 'semiannual':
            if date_from.month > 6:
                date_start = date_from + relativedelta(month=7, day=1)
                date_end = date_from + relativedelta(month=12, day=31)
            else:
                date_start = date_from + relativedelta(month=1, day=1)
                date_end = date_from + relativedelta(month=6, day=30)

        elif historic_type == 'annual':
            date_start = date_from + relativedelta(month=1, day=1)
            date_end = date_from + relativedelta(month=12, day=31)

        elif historic_type == 'last_year':
            date_start = date_from + relativedelta(years=-1, month=1, day=1)
            date_end = date_from + relativedelta(years=-1, month=12, day=31)

        elif historic_type == 'month':
            date_start = date_from
            date_end = date_to

        elif historic_type == 'start':
            date_start = self.contract_id.date_start
            date_end = date_to

        elif historic_type == 'three_months_ago':
            date_start = date_to + relativedelta(months=-3, day=1)
            date_end = date_from + relativedelta(days=-1)

        elif historic_type == 'last_three_months':
            date_start = date_to + relativedelta(months=-2, day=1)
            date_end = date_to

            if annual:
                date_start = max(date_start, initial_year)

        query = """
             SELECT sum(total)
             FROM hr_payslip_line
             WHERE code = %s AND employee_id = %s AND contract_id = %s
                 AND date_from <= %s AND date_to >= %s
         """
        self.env.cr.execute(query, (code, self.employee_id.id, self.contract_id.id, date_end, date_start))
        result = self.env.cr.fetchone()

        return result[0] if bool(result[0]) else 0

    def get_parameter(self, code: str):
        if not code:
            raise UserError(_("The code parameter is necessary."))
        parameter = self.env['hr.payroll.parameter'].search([('code', '=', code)])
        if parameter:
            line = parameter.line_ids.filtered(
                lambda l: l.date_start <= self.date_from <= l.date_end)
            return line.value
        else:
            raise UserError(_("The parameter %s does not exist." % code))

    def get_payslip_days(self):
        return days360(self.payroll_period_id.date_start, self.payroll_period_id.date_end + relativedelta(days=1))

    def get_360_days(self, date_a, date_b):
        return days360(date_a, date_b) + 1

    def get_relativedelta_years(self, date_a, date_b):
        return relativedelta(date_a, date_b).years

    def get_relativedelta_months(self, date_a, date_b):
        return relativedelta(date_a, date_b).months

    def get_relativedelta_days(self, date_a, date_b):
        return relativedelta(date_a, date_b).days

    def math_ceil(self, value):
        return math.ceil(value)

    def math_floor(self, value):
        return math.floor(value)

    def get_total_worked_days(self):
        return days360(max(self.date_liquidation + relativedelta(month=1, day=1), self.contract_id.date_start),
                       self.date_liquidation) + 1

    def get_total_leaves(self):
        leaves = 0
        codes = ['DIAS_AUSEN_NO_JUST', 'DIA_DESC_DOMINICAL', 'DIAS_LIC_NO_REM']
        for code in codes:
            leaves += self.get_history_values(code, 'start') + (
                    sum(self.line_ids.filtered(lambda l: l.code == code).mapped('total')) -
                    self.get_history_values(code, 'month'))
        return leaves

    def get_resignation_type_value(self):
        requisition_id = self.recruitment_requisition_id
        return dict(requisition_id._fields['resignation_type'].selection).get(requisition_id.resignation_type)

    def get_quantity_days(self, code):
        return sum(self.worked_days_line_ids.filtered(lambda l: l.code == code).mapped('number_of_days'))
