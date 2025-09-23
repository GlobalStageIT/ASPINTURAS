from odoo import models, fields, api, _

class ReportPayroll(models.AbstractModel):
    _name = "report.hr_payroll_custom.payslip_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Payroll"

    def _generate_header(self, sheet, workbook, table_header):
        # --- Estilos ---
        header_general = workbook.add_format({
            "bg_color": "#D9E1F2",   # Azul claro
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "font_size": 10,
            "bold": True
        })
        header_special = workbook.add_format({
            "bg_color": "#305496",   # Azul oscuro
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "font_size": 10,
            "font_color": "#FFFFFF",
            "bold": True
        })

        # Escribir encabezados
        for column, header in enumerate(table_header):
            if header in ["Total Devengado", "Total Deducciones", "Total"]:
                sheet.write(0, column, header, header_special)
            else:
                sheet.write(0, column, header, header_general)
            sheet.set_column(column, column, 20)  # ancho de columna estándar

        # Filtro automático
        sheet.autofilter(0, 0, 0, len(table_header) - 1)

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet("NÓMINA")

        # Encabezado de tabla dinámico
        header, earn, deduccion = self.get_header(records.line_ids)
        self._generate_header(sheet, workbook, header)

        # --- Estilos ---
        text_format = workbook.add_format({
            "align": "left",
            "valign": "vcenter",
            "font_size": 9
        })
        num_format = workbook.add_format({
            "num_format": '#,##0.00',
            "align": "right",
            "font_size": 9
        })
        num_bold = workbook.add_format({
            "num_format": '#,##0.00',
            "align": "right",
            "font_size": 9,
            "bold": True,
            "bg_color": "#E2EFDA",  # Verde suave para destacar totales
            "border": 1
        })

        row = 1
        for record in records:
            sheet.write(row, 0, record.employee_id.name or '', text_format)
            sheet.write(row, 1, record.employee_id.identification_id or '', text_format)
            sheet.write(row, 2, record.contract_id.name or '', text_format)
            sheet.write(row, 3, record.contract_id.date_start.strftime('%d/%m/%Y') if record.contract_id.date_start else '', text_format)
            sheet.write(row, 4, record.worked_days_total or '', text_format)

            column = 4
            # Devengados
            for obj in earn:
                column += 1
                sheet.write(row, column, self.get_data(record.line_ids, obj) or 0, num_format)
            column += 1
            sheet.write(row, column, record.accrued_total_amount or 0, num_bold)

            # Deducciones
            for obj in deduccion:
                column += 1
                sheet.write(row, column, self.get_data(record.line_ids, obj) or 0, num_format)
            column += 1
            sheet.write(row, column, record.deductions_total_amount or 0, num_bold)

            # Total neto
            column += 1
            sheet.write(row, column, record.total_amount or 0, num_bold)

            row += 1

    def get_data(self, line, cod):
        for obj in line:
            if obj.code == cod:
                return obj.total
        return 0

    def get_header(self, records):
        table_header = ['Nombre', 'Identificación', 'No contrato', 'Fecha de Ingreso', 'Días trabajados']
        earn = []
        deduction = []

        devengados = self.env['hr.salary.rule'].search([('type_concept', '=', 'earn')])
        deduccion = self.env['hr.salary.rule'].search([('type_concept', '=', 'deduction')])

        for obj in devengados:
            for record in records:
                if record.code == obj.code and obj.name not in table_header and record.total != 0:
                    table_header.append(obj.name)
                    earn.append(obj.code)

        table_header.append('Total Devengado')

        for obj in deduccion:
            for record in records:
                if record.code == obj.code and obj.name not in table_header and record.total != 0:
                    table_header.append(obj.name)
                    deduction.append(obj.code)

        table_header.append('Total Deducciones')
        table_header.append('Total')

        return table_header, earn, deduction
