# Autor: Diego Torres
# Desarrollador y Consultor Odoo
# Linkedln: https://www.linkedin.com/in/diego-felipe-torres-reyes-083091152/
# Email: 20diegotorres01@gmail.com
# Github: DiTo1005
# Cel. +57 3108804090

{
    'name': 'Modificaciones Base Empleado',
    'version': '18.1',
    'summary': 'Modificaciones modulo base de empleados',
    'description': """
        Este módulo realiza cambios base para empleados y modulos que dependan de el.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'category': 'Payslip',
    'depends': ['hr_skills','l10n_co_hr_payroll_custom'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/hr_employee_arl_risk_data.xml',
        'data/entity.type.csv',
        # Views
        'views/hr_contract_view.xml',
        'views/hr_employee_arl_risk.xml',
        'views/hr_employee_views.xml',
        'views/hr_resume_line_inherit.xml',
        'views/hr_resume_line_type_tree_view.xml',
        'views/hr_job_views.xml',
        'views/res_partner_view.xml',
        'menus.xml',
    ],
    'installable': True,
    'application': True,

}
