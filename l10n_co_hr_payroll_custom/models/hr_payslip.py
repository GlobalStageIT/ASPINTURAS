from odoo import fields, models, _, api
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_json_request(self):
        for rec in self:
            if not rec.number:
                raise UserError(_("The payroll must have a consecutive number, 'Reference' field"))
            if not rec.contract_id.payroll_period_id:
                raise UserError(_("The contract must have the 'Scheduled Pay' field configured"))
            if not rec.company_id.name:
                raise UserError(_("Your company does not have a name"))
            if not rec.company_id.type_document_identification_id:
                raise UserError(_("Your company does not have an identification type"))
            if not rec.company_id.vat:
                raise UserError(_("Your company does not have a document number"))
            if not rec.company_id.partner_id.postal_municipality_id:
                raise UserError(_("Your company does not have a postal municipality"))
            if not rec.company_id.street:
                raise UserError(_("Your company does not have an address"))
            if not rec.contract_id.type_worker_id:
                raise UserError(_("The contract must have the 'Type worker' field configured"))
            if not rec.contract_id.subtype_worker_id:
                raise UserError(_("The contract must have the 'Subtype worker' field configured"))
            if not rec.employee_id.private_first_name:
                raise UserError(_("Employee does not have a first name"))
            if not rec.employee_id.private_surname:
                raise UserError(_("Employee does not have a surname"))
            if not rec.employee_id.private_type_document_identification_id:
                raise UserError(_("Employee does not have an identification type"))
            if rec.employee_id.private_type_document_identification_id.id == 6:
                raise UserError(_("The employee's document type cannot be NIT"))
            if not rec.employee_id.private_vat:
                raise UserError(_("Employee does not have an document number"))
            if not rec.employee_id.private_postal_municipality_id:
                raise UserError(_("Employee does not have a postal municipality"))
            if not rec.employee_id.private_street:
                raise UserError(_("Employee does not have an address."))
            if not rec.contract_id.name:
                raise UserError(_("Contract does not have a name"))
            if rec.contract_id.wage <= 0:
                raise UserError(_("The contract must have the 'Wage' field configured"))
            if not rec.contract_id.type_contract_id:
                raise UserError(_("The contract must have the 'Type contract' field configured"))
            if not rec.contract_id.date_start:
                raise UserError(_("The contract must have the 'Start Date' field configured"))
            if not rec.date_from:
                raise UserError(_("The payroll must have a period"))
            if not rec.date_to:
                raise UserError(_("The payroll must have a period"))
            if not rec.payment_form_id:
                raise UserError(_("The payroll must have a payment form"))
            if not rec.payment_method_id:
                raise UserError(_("The payroll must have a payment method"))
            if not rec.payment_date:
                raise UserError(_("The payroll must have a payment date"))

            rec.edi_sync = rec.company_id.edi_payroll_is_not_test

            sequence = {}
            if rec.number and rec.number not in ('New', _('New')):
                sequence_number = ''.join([i for i in rec.number if i.isdigit()])
                sequence_prefix = rec.number.split(sequence_number)
                if sequence_prefix:
                    sequence = {
                        # "worker_code": "string",
                        "prefix": sequence_prefix[0],
                        "number": int(sequence_number)
                    }
                else:
                    raise UserError(_("The sequence must have a prefix"))

            information = {
                "payroll_period_code": rec.contract_id.payroll_period_id.id,
                "currency_code": 35,
                # "trm": 1
            }

            employer_id_code = rec.company_id.type_document_identification_id.id
            employer_id_number_general = ''.join([i for i in rec.company_id.vat if i.isdigit()])
            if employer_id_code == 6:
                employer_id_number = employer_id_number_general[:-1]
            else:
                employer_id_number = employer_id_number_general

            employer = {
                "name": rec.company_id.name,
                # "surname": "string",
                # "second_surname": "string",
                # "first_name": "string",
                # "other_names": "string",
                "id_code": employer_id_code,
                "id_number": employer_id_number,
                "country_code": 46,
                "municipality_code": rec.company_id.partner_id.postal_municipality_id.id,
                "address": rec.company_id.street
            }

            employee = {
                "type_worker_code": rec.contract_id.type_worker_id.id,
                "subtype_worker_code": rec.contract_id.subtype_worker_id.id,
                "high_risk_pension": rec.contract_id.high_risk_pension,
                "id_code": rec.employee_id.private_type_document_identification_id.id,
                "id_number": ''.join([i for i in rec.employee_id.private_vat if i.isdigit()]),
                "surname": rec.employee_id.private_surname,
                "first_name": rec.employee_id.private_first_name,
                "country_code": 46,
                "municipality_code": rec.employee_id.private_postal_municipality_id.id,
                "address": rec.employee_id.private_street,
                "integral_salary": rec.contract_id.integral_salary,
                "contract_code": rec.contract_id.type_contract_id.id,
                "salary": abs(rec.contract_id.wage),
                # "worker_code": "string"
            }
            if rec.employee_id.private_other_names:
                employee['other_names'] = rec.employee_id.private_other_names
            if rec.employee_id.private_second_surname:
                employee['second_surname'] = rec.employee_id.private_second_surname

            if rec.contract_id.date_end:
                amount_time = self.calculate_time_worked(rec.contract_id.date_start, rec.contract_id.date_end)
            else:
                amount_time = self.calculate_time_worked(rec.contract_id.date_start, rec.date_to)

            rec.date = fields.Date.context_today(rec)

            period = {
                "admission_date": fields.Date.to_string(rec.contract_id.date_start),
                "settlement_start_date": fields.Date.to_string(rec.date_from),
                "settlement_end_date": fields.Date.to_string(rec.date_to),
                "amount_time": amount_time,
                "date_issue": fields.Date.to_string(rec.date)
            }
            if rec.contract_id.date_end:
                period['withdrawal_date'] = fields.Date.to_string(rec.contract_id.date_end)

            payment = {
                "code": rec.payment_form_id.id,
                "method_code": rec.payment_method_id.id,
                # "bank": "string",
                # "account_type": "string",
                # "account_number": "string"
            }

            # Earn details
            basic = {}
            company_withdrawal_bonus = 0
            compensation = 0
            endowment = 0
            layoffs = {}
            primas = {}
            refund = 0
            sustainment_support = 0
            telecommuting = 0

            advances = []
            assistances = []
            bonuses = []
            commissions = []
            compensations = []
            overtimes_surcharges = []
            incapacities = []
            legal_strikes = []
            licensings_maternity_or_paternity_leaves = []
            licensings_permit_or_paid_licenses = []
            licensings_suspension_or_unpaid_leaves = []
            other_concepts = []
            third_party_payments = []
            transports = []
            vacation_common = []
            vacation_compensated = []
            vouchers = []

            # Deduction details
            deduction_afc = 0
            deduction_complementary_plans = 0
            deduction_cooperative = 0
            deduction_debt = 0
            deduction_education = 0
            deduction_health = {}
            deduction_pension_fund = {}
            deduction_pension_security_fund = {}
            deduction_refund = 0
            deduction_sanctions = {}
            deduction_tax_lien = 0
            deduction_trade_unions = {}
            deduction_voluntary_pension = 0
            deduction_withholding_source = 0

            deduction_advances = []
            deduction_libranzas = []
            deduction_others = []
            deduction_third_party_payments = []

            # Salary computation iteration
            for line_id in rec.line_ids:
                line_id.edi_rate = line_id.compute_edi_rate()
                line_id.edi_quantity = line_id.compute_edi_quantity()
                if line_id.salary_rule_id.type_concept == 'earn' and not line_id.salary_rule_id.edi_is_detailed:
                    if line_id.salary_rule_id.earn_category == 'basic':
                        if line_id.total:
                            # The days worked are calculated at the end
                            basic['worked_days'] = None
                            basic['worker_salary'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'company_withdrawal_bonus':
                        if line_id.total:
                            company_withdrawal_bonus = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'compensation':
                        if line_id.total:
                            compensation = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'endowment':
                        if line_id.total:
                            endowment = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'layoffs':
                        if line_id.total:
                            layoffs['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'layoffs_interest':
                        if line_id.total:
                            layoffs['percentage'] = abs(line_id.edi_rate)
                            layoffs['interest_payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'primas':
                        if line_id.total:
                            primas['quantity'] = abs(line_id.edi_quantity)
                            primas['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'primas_non_salary':
                        if line_id.total:
                            primas['non_salary_payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'refund':
                        if line_id.total:
                            refund = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'sustainment_support':
                        if line_id.total:
                            sustainment_support = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'telecommuting':
                        if line_id.total:
                            telecommuting = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'advances':
                        if line_id.total:
                            advances.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'assistances':
                        if line_id.total:
                            assistances.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'assistances_non_salary':
                        if line_id.total:
                            assistances.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'bonuses':
                        if line_id.total:
                            bonuses.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'bonuses_non_salary':
                        if line_id.total:
                            bonuses.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'commissions':
                        if line_id.total:
                            commissions.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'compensations_extraordinary':
                        if line_id.total:
                            compensations.append({
                                "extraordinary": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'compensations_ordinary':
                        if line_id.total:
                            compensations.append({
                                "ordinary": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'daily_overtime':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 1,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'daily_surcharge_hours_sundays_holidays':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 5,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'hours_night_surcharge':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 3,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_common':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 1,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_professional':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 2,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_working':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 3,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'legal_strikes':
                        if line_id.edi_quantity:
                            legal_strikes.append({
                                "quantity": abs(line_id.edi_quantity)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_maternity_or_paternity_leaves':
                        if line_id.edi_quantity and line_id.total:
                            licensings_maternity_or_paternity_leaves.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_permit_or_paid_licenses':
                        if line_id.edi_quantity and line_id.total:
                            licensings_permit_or_paid_licenses.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_suspension_or_unpaid_leaves':
                        if line_id.edi_quantity:
                            licensings_suspension_or_unpaid_leaves.append({
                                "quantity": abs(line_id.edi_quantity)
                            })
                    elif line_id.salary_rule_id.earn_category == 'other_concepts':
                        if line_id.total:
                            other_concepts.append({
                                "description": line_id.name,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'other_concepts_non_salary':
                        if line_id.total:
                            other_concepts.append({
                                "description": line_id.name,
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'overtime_night_hours':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 2,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_holiday_daily_overtime':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 4,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_holidays_night_surcharge_hours':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 7,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_night_overtime_holidays':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 6,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'third_party_payments':
                        if line_id.total:
                            third_party_payments.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_assistance':
                        if line_id.total:
                            transports.append({
                                'assistance': abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_non_salary_viatic':
                        if line_id.total:
                            transports.append({
                                "non_salary_viatic": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_viatic':
                        if line_id.total:
                            transports.append({
                                "viatic": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vacation_common':
                        if line_id.edi_quantity and line_id.total:
                            vacation_common.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vacation_compensated':
                        if line_id.edi_quantity and line_id.total:
                            vacation_compensated.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers':
                        if line_id.total:
                            vouchers.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_non_salary':
                        if line_id.total:
                            vouchers.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_non_salary_food':
                        if line_id.total:
                            vouchers.append({
                                "non_salary_food_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_salary_food':
                        if line_id.total:
                            vouchers.append({
                                "salary_food_payment": abs(line_id.total)
                            })
                elif line_id.salary_rule_id.type_concept == 'deduction' \
                        and not line_id.salary_rule_id.edi_is_detailed \
                        and line_id.total:
                    if line_id.salary_rule_id.deduction_category == 'afc':
                        deduction_afc = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'complementary_plans':
                        deduction_complementary_plans = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'cooperative':
                        deduction_cooperative = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'debt':
                        deduction_debt = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'education':
                        deduction_education = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'health':
                        deduction_health['percentage'] = abs(line_id.edi_rate)
                        deduction_health['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_fund':
                        deduction_pension_fund['percentage'] = abs(line_id.edi_rate)
                        deduction_pension_fund['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_security_fund':
                        deduction_pension_security_fund['percentage'] = abs(line_id.edi_rate)
                        deduction_pension_security_fund['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_security_fund_subsistence':
                        deduction_pension_security_fund['percentage_subsistence'] = abs(line_id.edi_rate)
                        deduction_pension_security_fund['payment_subsistence'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'refund':
                        deduction_refund = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'sanctions_private':
                        deduction_sanctions['payment_private'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'sanctions_public':
                        deduction_sanctions['payment_public'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'tax_lien':
                        deduction_tax_lien = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'trade_unions':
                        deduction_trade_unions = {
                            'percentage': abs(line_id.edi_rate),
                            'payment': abs(line_id.total)
                        }
                    elif line_id.salary_rule_id.deduction_category == 'voluntary_pension':
                        deduction_voluntary_pension = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'withholding_source':
                        deduction_withholding_source = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'advances':
                        deduction_advances.append({
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'libranzas':
                        deduction_libranzas.append({
                            "description": line_id.salary_rule_id.name,
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'other_deductions':
                        deduction_others.append({
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'third_party_payments':
                        deduction_third_party_payments.append({
                            "payment": abs(line_id.total)
                        })

            # Calculate days worked considering settlement flag
            if rec.is_settlement:
                rec.worked_days_total = 0
            else:
                rec.worked_days_total = self.calculate_time_worked(rec.date_from, rec.date_to)
                for list_with_days in [
                    vacation_common,
                    licensings_maternity_or_paternity_leaves,
                    licensings_permit_or_paid_licenses,
                    licensings_suspension_or_unpaid_leaves,
                    incapacities,
                    legal_strikes
                ]:
                    for dict_with_days in list_with_days:
                        rec.worked_days_total -= dict_with_days['quantity']

            worked_days_total = rec.line_ids.filtered(lambda l: l.code == 'DIAS_SUELDO').total
            rec.worked_days_total = worked_days_total if worked_days_total > 0 else 0
            basic['worked_days'] = rec.worked_days_total

            # Complete json request
            earn = {
                "basic": basic
            }

            # Earn details
            vacation = {}
            if vacation_common:
                vacation['common'] = vacation_common
            if vacation_compensated:
                vacation['compensated'] = vacation_compensated
            if vacation:
                earn['vacation'] = vacation

            if primas:
                if 'payment' in primas:
                    earn['primas'] = primas
                else:
                    raise UserError(_("The 'Primas' rule is mandatory in order to report Primas"))

            if layoffs:
                if ('payment' in layoffs) and ('interest_payment' in layoffs):
                    earn['layoffs'] = layoffs
                else:
                    raise UserError(
                        _("The 'Layoffs' and 'Layoffs interest' rules are mandatory in order to report Layoffs"))

            licensings = {}
            if licensings_maternity_or_paternity_leaves:
                licensings['licensings_maternity_or_paternity_leaves'] = licensings_maternity_or_paternity_leaves
            if licensings_permit_or_paid_licenses:
                licensings['licensings_permit_or_paid_licenses'] = licensings_permit_or_paid_licenses
            if licensings_suspension_or_unpaid_leaves:
                licensings['licensings_suspension_or_unpaid_leaves'] = licensings_suspension_or_unpaid_leaves
            if licensings:
                earn['licensings'] = licensings

            if endowment:
                earn['endowment'] = endowment

            if sustainment_support:
                earn['sustainment_support'] = sustainment_support

            if telecommuting:
                earn['telecommuting'] = telecommuting

            if company_withdrawal_bonus:
                earn['company_withdrawal_bonus'] = company_withdrawal_bonus

            if compensation:
                earn['compensation'] = compensation

            if refund:
                earn['refund'] = refund

            if transports:
                earn['transports'] = transports

            if overtimes_surcharges:
                earn['overtimes_surcharges'] = overtimes_surcharges

            if incapacities:
                earn['incapacities'] = incapacities

            if bonuses:
                earn['bonuses'] = bonuses

            if assistances:
                earn['assistances'] = assistances

            if legal_strikes:
                earn['legal_strikes'] = legal_strikes

            if other_concepts:
                earn['other_concepts'] = other_concepts

            if compensations:
                earn['compensations'] = compensations

            if vouchers:
                earn['vouchers'] = vouchers

            if commissions:
                earn['commissions'] = commissions

            if third_party_payments:
                earn['third_party_payments'] = third_party_payments

            if advances:
                earn['advances'] = advances

            # Deduction details
            deduction = {}

            if deduction_health:
                deduction['health'] = deduction_health

            if deduction_pension_fund:
                deduction['pension_fund'] = deduction_pension_fund

            if deduction_pension_security_fund:
                deduction['pension_security_fund'] = deduction_pension_security_fund

            if deduction_voluntary_pension:
                deduction['voluntary_pension'] = deduction_voluntary_pension

            if deduction_withholding_source:
                deduction['withholding_source'] = deduction_withholding_source

            if deduction_afc:
                deduction['afc'] = deduction_afc

            if deduction_cooperative:
                deduction['cooperative'] = deduction_cooperative

            if deduction_tax_lien:
                deduction['tax_lien'] = deduction_tax_lien

            if deduction_complementary_plans:
                deduction['complementary_plans'] = deduction_complementary_plans

            if deduction_education:
                deduction['education'] = deduction_education

            if deduction_refund:
                deduction['refund'] = deduction_refund

            if deduction_debt:
                deduction['debt'] = deduction_debt

            if deduction_trade_unions:
                deduction['trade_unions'] = [deduction_trade_unions]

            if deduction_sanctions:
                if 'payment_public' not in deduction_sanctions:
                    deduction_sanctions['payment_public'] = 0.0
                if 'payment_private' not in deduction_sanctions:
                    deduction_sanctions['payment_private'] = 0.0
                deduction['sanctions'] = [deduction_sanctions]

            if deduction_libranzas:
                deduction['libranzas'] = deduction_libranzas

            if deduction_third_party_payments:
                deduction['third_party_payments'] = deduction_third_party_payments

            if deduction_advances:
                deduction['advances'] = deduction_advances

            if deduction_others:
                deduction['other_deductions'] = deduction_others

            # Payment
            payment_dates = [{
                "date": fields.Date.to_string(rec.payment_date)
            }]

            json_request = {}
            json_request['sync'] = rec.edi_sync
            # json_request["rounding"] = 0
            json_request['accrued_total'] = rec.accrued_total_amount
            json_request['deductions_total'] = rec.deductions_total_amount
            json_request['total'] = rec.total_amount
            if sequence:
                json_request['sequence'] = sequence
            json_request['information'] = information
            # json_request["novelty"] = novelty
            # json_request["provider"] = provider
            json_request['employer'] = employer
            json_request['employee'] = employee
            json_request['period'] = period
            json_request['payment'] = payment
            json_request['payment_dates'] = payment_dates
            json_request['earn'] = earn

            # Optionals
            if deduction:
                json_request['deduction'] = deduction

            if rec.note:
                notes = [{
                    "text": rec.note
                }]
                json_request['notes'] = notes

            # Credit note
            if rec.credit_note:
                if rec.origin_payslip_id:
                    if rec.origin_payslip_id.edi_is_valid:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.edi_number,
                            'uuid': rec.origin_payslip_id.edi_uuid,
                            'issue_date': str(rec.origin_payslip_id.edi_issue_date)
                        }
                    else:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.number,
                            'issue_date': str(rec.origin_payslip_id.date)
                        }
                else:
                    raise UserError(_("The Origin payslip is required for adjusment notes."))

                json_request = rec.get_json_delete_request(json_request)

            return json_request

    # def action_compute_sheet(self):
    #     res = super(HrPayslip, self).action_compute_sheet()
    #     for payslip in self:
    #         payslip.compute_totals()
    #
    #     return res