/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.AdiHelpdeskEmailCheck = publicWidget.Widget.extend({
    selector: "form#helpdesk_ticket_form",

    events: {
        "input input[name='adi_submitted_email']": "_onEmailInput",
        "keydown input[name='adi_submitted_email']": "_onEmailKeydown",
        "click .adi_verify_email_button": "_onVerifyEmail",
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

        this.verifyButton = this.el.querySelector(
            ".adi_verify_email_button"
        );

        this.ticketDetailsSection = this.el.querySelector(
            "#adi_ticket_details_section"
        );

        this.message = this.el.querySelector(
            ".adi_email_check_message"
        );

        if (
            !this.emailInput ||
            !this.nameInput ||
            !this.companyInput ||
            !this.verifyButton ||
            !this.ticketDetailsSection ||
            !this.message
        ) {
            return;
        }

        this.nameGroup =
            this.nameInput.closest(".s_website_form_field") ||
            this.nameInput.parentElement;

        this.companyGroup =
            this.companyInput.closest(".s_website_form_field") ||
            this.companyInput.parentElement;

        this._requestNumber = 0;

        this._hideExtraDetails();
        this._hideTicketDetails();
        this._clearMessage();
    },

    _onEmailInput() {
        this._requestNumber++;

        this._clearMessage();
        this._hideExtraDetails();
        this._hideTicketDetails();

        this.verifyButton.disabled = false;
        this.emailInput.disabled = false;
    },

    _onEmailKeydown(event) {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        this._verifyEmail();
    },

    _onVerifyEmail() {
        this._verifyEmail();
    },

    async _verifyEmail() {

        const email = (this.emailInput.value || "").trim();

        if (!email || !this.emailInput.checkValidity()) {
            this._requestNumber++;

            this._hideExtraDetails();
            this._hideTicketDetails();

            this._setMessage(
                "Please enter a valid email address."
            );

            this.emailInput.focus();
            return;
        }

        const requestNumber = ++this._requestNumber;

        this.verifyButton.disabled = true;
        this.emailInput.disabled = true;

        this._hideExtraDetails();
        this._hideTicketDetails();

        this._setMessage(
            "Checking your details..."
        );

        try {

            const result = await jsonrpc(
                "/adi/helpdesk/check_email",
                {
                    email,
                }
            );

            if (
                requestNumber !== this._requestNumber
            ) {
                return;
            }

            if (result.recognised) {

                this._hideExtraDetails();

                this._setMessage(
                    "Email recognised. Please continue."
                );

            } else {

                this._showExtraDetails();

                this._setMessage(
                    "We could not match this email. Please provide your contact and company details."
                );
            }

            this._showTicketDetails();

        } catch {

            if (
                requestNumber !== this._requestNumber
            ) {
                return;
            }

            this._hideExtraDetails();
            this._hideTicketDetails();

            this._setMessage(
                "The email address could not be checked. Please try again."
            );

        } finally {

            if (
                requestNumber === this._requestNumber
            ) {
                this.verifyButton.disabled = false;
                this.emailInput.disabled = false;
            }
        }
    },

    _showTicketDetails() {
        this.ticketDetailsSection.classList.remove("d-none");
    },

    _hideTicketDetails() {
        this.ticketDetailsSection.classList.add("d-none");
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