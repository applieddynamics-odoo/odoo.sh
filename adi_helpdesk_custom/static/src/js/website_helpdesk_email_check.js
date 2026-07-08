/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.AdiHelpdeskEmailCheck = publicWidget.Widget.extend({
    selector: "form",

    events: {
        "change input[name='adi_submitted_email']": "_onEmailChanged",
        "blur input[name='adi_submitted_email']": "_onEmailChanged",
    },

    start() {
        this._super(...arguments);

        this.emailInput = this.el.querySelector("input[name='adi_submitted_email']");
        this.nameInput = this.el.querySelector("input[name='adi_submitted_contact_name']");
        this.companyInput = this.el.querySelector("input[name='adi_submitted_company_name']");

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

        this.message = this.emailInput.parentElement.querySelector(".adi_email_check_message");

        if (!this.message) {
            this.message = document.createElement("div");
            this.message.className = "adi_email_check_message text-muted mt-2";
            this.emailInput.insertAdjacentElement("afterend", this.message);
        }

        this.message.textContent = "";

        this._hideExtraDetails();
    },

    async _onEmailChanged() {
        const email = (this.emailInput.value || "").trim();

        if (!email || !email.includes("@")) {
            this._hideExtraDetails();
            this.message.textContent = "";
            return;
        }

        const result = await jsonrpc("/adi/helpdesk/check_email", { email });

        if (result.recognised) {
            this._hideExtraDetails();
            this.message.textContent = "Email recognised. You can continue.";
        } else {
            this._showExtraDetails();
            this.message.textContent = "Please provide your contact and company details below.";
        }
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