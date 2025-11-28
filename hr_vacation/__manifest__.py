# Autor: Diego Torres
# Desarrollador y Consultor Odoo
# Linkedln: https://www.linkedin.com/in/diego-felipe-torres-reyes-083091152/
# Email: 20diegotorres01@gmail.com
# Github: DiTo1005
# Cel. +57 3108804090

{
    'name': 'Modulo de Vacaciones',
    'icon': '/hr_vacation/static/description/icon.png',
    'version': '1.0',
    'summary': 'Modificaciones en el proceso de ausencias con vacaciones',
    'description': """
        Este módulo realiza cambios en el proceso y campos en las vacaciones provisionadas.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'website': 'https://www.linktic.com',
    'category': 'Human Resources',
    'depends': ['hr_novelty', 'hr_holidays_custom'],
    'data': [
        # Security
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        #Data
        'data/ir_cron_data.xml',
        # Views
        'views/hr_leave_view.xml',
        'views/hr_leave_view_action.xml',
        'views/hr_novelty_view.xml',
        'views/hr_vacation_views.xml',
        'views/hr_leave_type_view.xml',
        'menus.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
