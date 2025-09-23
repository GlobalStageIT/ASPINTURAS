from odoo import models, fields, api

class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    education_level = fields.Selection([
        ('pregrado', 'Pregrado'),
        ('posgrado', 'Posgrado'),
    ], string="Nivel Educativo")

    is_education = fields.Boolean(string="Es Educación", compute='_compute_is_education', store=True)

    @api.depends('line_type_id.name')
    def _compute_is_education(self):
        for record in self:
            record.is_education = record.line_type_id.name == 'Educación'

class HrResumeLineType(models.Model):
    _inherit = 'hr.resume.line.type'

    type = fields.Selection(selection=[('study', 'Study'),
                                       ('experience', 'Experience'),],string='Type')