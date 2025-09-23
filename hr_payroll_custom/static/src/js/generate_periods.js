/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class GeneratePeriodController extends ListController {
   setup() {
       super.setup();
   }

   generatePayrollPeriod() {
       this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'generate.payroll.period',
          name:'Generate Payroll Period',
          view_mode: 'form',
          view_type: 'form',
          views: [[false, 'form']],
          target: 'new',
          res_id: false,
      });
   }
}


registry.category("views").add("list_view_button", {
   ...listView,
   Controller: GeneratePeriodController,
   buttonTemplate: "generate_periods.ListView.Buttons",
});