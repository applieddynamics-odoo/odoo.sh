/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.AdiHelpdeskEmailCheck = publicWidget.Widget.extend({
    selector: "form",

    events: {
        "input input[name='adi_submitted_email']": "_onEmailInput",
        "blur input[name='adi_submitted_email']": "_onEmailChanged",
        "keydown input[name='adi_submitted_email']": "_onEmailKeydown",
    },

    start() {
        this._super(...arguments);

        this.emailInput = this.el.querySelector(
            "input[name='adi_submitted_email']"
        );
        this.nameInput = this.el.querySelector(
            "input[name='adi_submitted_contact_name']"
        );
        this.companyInput = this.el.querySelector(
            "input[name='adi_submitted_company_name']"
        );

        if (!this.emailInput || !this.nameInput || !this.companyInput) {
            return;
        }

        this.nameGroup =
            this.nameInput.closest(".s_website_form_field") ||
            this.nameInput.closest(".form-group") ||
            this.nameInput.parentElement;

        this.companyGroup =
            this.companyInput.closest(".s_website_form_field") ||
            this.companyInput.closest(".form-group") ||
            this.companyInput.parentElement;

        /*
         * Keep one status element only. Searching the whole form catches
         * messages created by an earlier version of this script or already
         * present in the website template.
         */

        /*
        * Limit message cleanup to the Submitted Email field.
        * The Website Editor may have stored old generated message divs,
        * so remove those and retain one controlled status element.
        */
        this.emailGroup =
            this.emailInput.closest(".s_website_form_field") ||
            this.emailInput.parentElement;

        /*
        * Remove any old generated help/status divs beneath the email input,
        * except for the message element managed by this widget.
        */
        const existingControlledMessage =
            this.emailGroup.querySelector(".adi_email_check_message");

        for (const element of [
            ...this.emailGroup.querySelectorAll(".text-muted.mt-2"),
        ]) {
            if (element !== existingControlledMessage) {
                element.remove();
            }
        }

        this.message = existingControlledMessage;

        if (!this.message) {
            this.message = document.createElement("div");
            this.emailInput.insertAdjacentElement(
                "afterend",
                this.message
            );
        }

        /*
        * Always reset the controlled element to one known state.
        */
        this.message.className =
            "adi_email_check_message text-muted mt-2 d-none";
        this.message.textContent = "";

        this._requestNumber = 0;

        this._hideExtraDetails();
        this._clearMessage();

    },

    _onEmailInput() {
        /*
        * Invalidate any lookup already running and immediately clear stale
        * results while the user edits the address.
        */
        this._requestNumber += 1;
        this._clearMessage();

        const email = (this.emailInput.value || "").trim();

        if (!email) {
            this._hideExtraDetails();
        }
    },

    _onEmailKeydown(event) {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        this._onEmailChanged();
    },


    async _onEmailChanged() {

        const email = (this.emailInput.value || "").trim();

        if (!email || !email.includes("@")) {
            this._requestNumber += 1;
            this._hideExtraDetails();
            this._clearMessage();
            return;
        }

        const requestNumber = ++this._requestNumber;

        this._clearMessage();

        try {
            const result = await jsonrpc(
                "/adi/helpdesk/check_email",
                { email }
            );

            /*
             * Ignore stale responses if the user changed or cleared the
             * address while this request was running.
             */
            if (
                requestNumber !== this._requestNumber ||
                email !== (this.emailInput.value || "").trim()
            ) {
                return;
            }

            if (result.recognised) {
                this._hideExtraDetails();
                this._setMessage(
                    "Email recognised. You can continue."
                );
            } else {
                this._showExtraDetails();
                this._setMessage(
                    "Please provide your contact and company details below."
                );
            }
        } catch {
            if (requestNumber !== this._requestNumber) {
                return;
            }

            this._hideExtraDetails();
            this._setMessage(
                "The email address could not be checked. Please try again."
            );
        }
    },

    _setMessage(text) {
        this.message.textContent = text;
        this.message.classList.remove("d-none");
    },

    _clearMessage() {
        this.message.textContent = "";
        this.message.classList.add("d-none");
    },

    _hideExtraDetails() {
        this.nameGroup.classList.add("d-none");
        this.companyGroup.classList.add("d-none");
        this.nameInput.required = false;
        this.companyInput.required = false;
    },

    _showExtraDetails() {
        this.nameGroup.classList.remove("d-none");
        this.companyGroup.classList.remove("d-none");
        this.nameInput.required = true;
        this.companyInput.required = true;
    },
});