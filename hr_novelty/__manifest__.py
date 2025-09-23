{
    'name': 'Novedades de Nómina',
    'version': '18.1',
    'summary': 'Gestión de novedades para la nómina',
    'description': """
        Este módulo permite gestionar las novedades de nómina para la empresa.
        Permite registrar y procesar diversas novedades que afectan el cálculo de la nómina.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr_payroll_custom', 'hr_holidays'],
    'data': [
        # Data
        'data/hr_novelty_data.xml',
        'data/ir_sequence.xml',
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        # Views
        'views/hr_novelty_type_view.xml',
        'views/hr_novelty_view.xml',
        'views/hr_payroll_period_view.xml',
        'menus.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
