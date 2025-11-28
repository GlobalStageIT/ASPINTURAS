# Autor: Diego Torres
# Desarrollador y Consultor Odoo
# Linkedln: https://www.linkedin.com/in/diego-felipe-torres-reyes-083091152/
# Email: 20diegotorres01@gmail.com
# Github: DiTo1005
# Cel. +57 3108804090

{
    'name': 'Modificaciones Base Nómina',
    'version': '18.1',
    'summary': 'Modificaciones en el proceso de nómina',
    'description': """
        Este módulo realiza cambios en el proceso y campos del proceso de talento humano para la empresa.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'category': 'Payslip',
    'depends': ['hr_payroll_account_community', 'hr_custom', 'report_xlsx'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        # Report
        'report/report_payslip.xml',
        'report/reports_xlsx.xml',
        # Data
        'data/hr_contribution_register_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_payment_frequency_data.xml',
        'data/mail_template.xml',
        # Views
        'views/account_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_contribution_register_view.xml',
        'views/hr_parameter_views.xml',
        'views/hr_payslip_line_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_payroll_period_views.xml',
        'views/hr_payment_frequency_views.xml',
        'views/hr_payslip_run_type_views.xml',
        'views/resource_calendar_view.xml',
        'menus.xml',
        # Wizard
        'wizard/generate_payroll_period.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_payroll_custom/static/src/xml/base.xml',
            'hr_payroll_custom/static/src/js/generate_periods.js',
        ],
    },
    'installable': True,
    'application': True,

}
