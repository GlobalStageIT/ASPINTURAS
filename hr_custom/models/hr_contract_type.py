from odoo import models, fields, api


class HrContractType(models.Model):
    _inherit = "hr.contract.type"
    _description = "Inheriting from hr.contract model to add fields"

    is_hour = fields.Boolean(string="Contract Hours")
