/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

patch(Many2OneField.prototype, {
    get Many2XAutocompleteProps() {
        const props = super.Many2XAutocompleteProps;

        /*
         * ADI Helpdesk Charge To selectors already have a tightly
         * controlled customer/order domain, so Search More adds no value.
         */
        if (
            this.props.name === "adi_charge_to_order_id" &&
            this.context.adi_helpdesk_charge_to
        ) {
            return {
                ...props,
                noSearchMore: true,
            };
        }

        return props;
    },
});