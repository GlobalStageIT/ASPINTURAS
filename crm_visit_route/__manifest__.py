# -*- coding: utf-8 -*-
{
    "name": "CRM Visit Route",
    "version": "18.0.5.0",
    "summary": "Planificación de visitas, rutas, geolocalización y auditoría",
    "depends": ["base", "crm", "sale_management"],
    "license": "LGPL-3",
    "category": "Sales/CRM",
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
    "data": [
        "security/ir.model.access.csv",
        "data/crm_visit_sequences.xml",
        "data/ir_cron_crm_visit_plan.xml",
        "data/server_actions.xml",
        "data/cleanup_actions.xml",
        "views/crm_menus_actions.xml",
        "views/crm_visit_views.xml",
        "views/crm_visit_plan_views.xml",
        "views/crm_visit_zone_views.xml",
        "views/crm_visit_optimize_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "views/client_actions.xml",
        "views/sale_order_slim_view.xml",
        "views/crm_visit_audit_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "crm_visit_route/static/src/js/gps_capture.js",
            "crm_visit_route/static/src/xml/gps_capture.xml",
        ]
    },
}
