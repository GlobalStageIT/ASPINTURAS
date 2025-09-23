{
    'name': 'Gestión de Prestamos',
    'version': '1.0',
    'summary': 'Gestión de prestamos para los empelados de la nómina de LinkTic SAS',
    'description': """
        Este módulo permite gestionar los prestamos de cada empleado en nómina para la empresa LinkTic SAS.
        Permite registrar y procesar diversos prestamos afectan el cálculo de la nómina.
    """,
    'author': 'Diego Felipe Torres Reyes',
    'license': 'AGPL-3',
    'website': 'https://www.linktic.com',
    'category': 'Human Resources',
    'depends': ['hr_novelty'],  # Dependencias de otros módulos
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/hr_loan_view.xml',
        'views/hr_loan_type_view.xml',
        'views/hr_contribution_register_view.xml',
        'views/hr_novelty_type_view.xml',
        # Data
        'data/ir_sequence.xml',
        # Menus
        'menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}


