/** @odoo-module **/

import { Message } from "@mail/core/common/message_model";
import { fields } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";

patch(Message.prototype, {
    setup() {
        super.setup(...arguments);

        this.adi_is_internal_author = fields.Attr(false);
        this.adi_body_already_green = fields.Attr(false);
    },
});
