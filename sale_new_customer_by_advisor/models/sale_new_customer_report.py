from odoo import fields, models, tools

class SaleNewCustomerReport(models.Model):
    _name = "sale.new.customer.report"
    _auto = False

    order_name = fields.Char()
    date_order_date = fields.Date()
    partner_id = fields.Many2one("res.partner")
    customer_vat = fields.Char()
    advisor_id = fields.Many2one("res.users")
    amount_total = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency")
    new_customer_count = fields.Integer()

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    so.id,
                    so.name as order_name,
                    so.date_order::date as date_order_date,
                    so.partner_id,
                    rp.vat as customer_vat,
                    so.x_studio_many2one_field_KSIG0 as advisor_id,
                    so.amount_total,
                    so.currency_id,
                    1 as new_customer_count
                FROM sale_order so
                JOIN res_partner rp ON rp.id = so.partner_id
                WHERE so.state IN ('sale','done')
            )
        """ % self._table)
