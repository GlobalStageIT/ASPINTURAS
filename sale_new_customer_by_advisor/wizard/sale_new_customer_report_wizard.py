from odoo import fields, models

class SaleNewCustomerReportWizard(models.TransientModel):
    _name = "sale.new.customer.report.wizard"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    advisor_id = fields.Many2one("res.users")

    def action_open_report(self):
        action = self.env.ref(
            "sale_new_customer_by_advisor.action_sale_new_customer_report"
        ).read()[0]

        domain = [
            ("date_order_date", ">=", self.date_from),
            ("date_order_date", "<=", self.date_to),
        ]

        if self.advisor_id:
            domain.append(("advisor_id", "=", self.advisor_id.id))

        action["domain"] = domain
        return action
