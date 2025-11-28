from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    job_type = fields.Selection([
        ('president', 'Presidente'),
        ('vice_president', 'Vicepresidente'),
        ('director', 'Director'),
        ('department_manager', 'Gerente Procesos'),
        ('project_manager', 'Gerente Proyectos'),
        ('operational_staff', 'Personal Operativo'),
    ], string="Tipo de puesto de trabajo")