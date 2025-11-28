# Autor: Diego Torres
# Desarrollador y Consultor Odoo
# Linkedln: https://www.linkedin.com/in/diego-felipe-torres-reyes-083091152/
# Email: 20diegotorres01@gmail.com
# Github: DiTo1005
# Cel. +57 3108804090

{
    'name': 'Modificación Nómina electrónica DIAN para Colombia',
    'version': '18.1',
    'summary': 'Modificaciones en el proceso de nómina electronica',
    'description': """
        Este módulo realiza cambios al modulo base de nómina de Jorels.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'category': 'Payslip',
    'depends': ['l10n_co_hr_payroll', 'hr_payroll_community'],
    'data': [
        # Views
        'views/hr_payslip_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_contract_type_view.xml',
    ],
    'installable': True,
    'application': True,

}
