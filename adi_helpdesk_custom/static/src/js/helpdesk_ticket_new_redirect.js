/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

function shouldRedirectToNewTicketWizard(controller) {
    return controller.props.resModel === "helpdesk.ticket";
}

function openNewTicketWizard(controller) {
    return controller.actionService.doAction(
        "adi_helpdesk_custom.action_adi_helpdesk_new_ticket_wizard"
    );
}

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
    },

    async createRecord() {
        if (shouldRedirectToNewTicketWizard(this)) {
            return openNewTicketWizard(this);
        }

        return super.createRecord(...arguments);
    },
});

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
    },

    async create() {
        if (shouldRedirectToNewTicketWizard(this)) {
            return openNewTicketWizard(this);
        }

        return super.create(...arguments);
    },
});