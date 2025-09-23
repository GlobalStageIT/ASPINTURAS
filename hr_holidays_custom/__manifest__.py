# Autor: Diego Torres
# Desarrollador y Consultor Odoo
# Linkedln: https://www.linkedin.com/in/diego-felipe-torres-reyes-083091152/
# Email: 20diegotorres01@gmail.com
# Github: DiTo1005
# Cel. +57 3108804090

{
    'name': 'Modulo de Ausencias Custom',
    'icon': '/hr_holidays_custom/static/description/icon.png',
    'version': '18.0',
    'summary': 'Modificaciones en el proceso de ausencias',
    'description': """
        Este módulo realiza cambios en el proceso y campos en las ausencias.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'website': 'https://www.linktic.com',
    'category': 'Human Resources',
    'depends': ['hr_payroll_custom'],
    'data': [
        # Views
        'views/hr_leave_type_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_leave_allocation_view.xml',
        'menus.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
