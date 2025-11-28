/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class GpsCapture extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ loading: true, error: null });
        onMounted(() => this.capture());
    }

    async capture() {
        try {
            const ctx = (this.props.action && this.props.action.context) || {};
            const activeId = ctx.active_id;
            if (!activeId) {
                this.notification.add("No hay registro activo.", { type: "warning" });
                return;
            }
            if (!("geolocation" in navigator)) {
                this.notification.add("Geolocalización no soportada en este dispositivo.", { type: "danger" });
                return;
            }
            // Uso estándar de la API de geolocalización, igual que Odoo en contactos.
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    try {
                        const lat = pos.coords.latitude;
                        const lng = pos.coords.longitude;
                        await this.orm.call("crm.visit", "action_geocheck", [[activeId], lat, lng]);
                        this.notification.add("Coordenadas registradas correctamente.", { type: "success" });
                        this.action.doAction({ type: "ir.actions.act_window_close" });
                    } catch (e) {
                        console.error(e);
                        this.notification.add("Error al guardar coordenadas.", { type: "danger" });
                    }
                },
                (err) => {
                    console.error(err);
                    let msg = "No se pudo obtener la ubicación.";
                    if (err && err.message) {
                        msg += " " + err.message;
                    }
                    this.state.error = msg;
                    this.notification.add(msg, { type: "danger" });
                },
                { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
            );
        } finally {
            this.state.loading = false;
        }
    }

    get message() {
        if (this.state.loading) {
            return "Obteniendo coordenadas…";
        }
        if (this.state.error) {
            return this.state.error;
        }
        return "Operación completada.";
    }

    static template = "crm_visit_route.GpsCapture";
}

registry.category("actions").add("crm_visit_route.gps_capture", GpsCapture);
