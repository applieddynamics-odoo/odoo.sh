/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

const SUBMISSION_RESET_FLAG = "adi_helpdesk_ticket_submitted";

publicWidget.registry.AdiHelpdeskEmailCheck = publicWidget.Widget.extend({
    selector: "form#helpdesk_ticket_form",

    events: {
        "input input[name='adi_submitted_email']": "_onEmailInput",
        "keydown input[name='adi_submitted_email']": "_onEmailKeydown",
        "click .adi_verify_email_button": "_onVerifyEmail",
    },

    start() {
        const result = this._super(...arguments);

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

        this.verifiedBadge = this.el.querySelector(
            ".adi_email_verified_badge"
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
            !this.verifiedBadge ||
            !this.ticketDetailsSection ||
            !this.message
        ) {
            return result;
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
        this._showVerifyButton();

        /*
         * The pageshow event also fires when the browser restores this page
         * from its back/forward cache.
         */
        this._boundPageShow = this._onPageShow.bind(this);

        window.addEventListener(
            "pageshow",
            this._boundPageShow
        );

        this._resetAfterSubmissionIfNeeded();

        return result;
    },

    destroy() {
        if (this._boundPageShow) {
            window.removeEventListener(
                "pageshow",
                this._boundPageShow
            );
        }

        return this._super(...arguments);
    },

    _onEmailInput() {
        /*
         * Invalidate any earlier lookup and return the form to its initial
         * verification state whenever the email address changes.
         */
        this._requestNumber += 1;

        this._clearMessage();
        this._hideExtraDetails();
        this._hideTicketDetails();
        this._showVerifyButton();

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
            this._requestNumber += 1;

            this._hideExtraDetails();
            this._hideTicketDetails();
            this._showVerifyButton();

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
        this._showVerifyButton();

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

            /*
             * Ignore an obsolete response if another lookup has started.
             */
            if (requestNumber !== this._requestNumber) {
                return;
            }

            if (result.recognised) {
                this._hideExtraDetails();

                this._setMessage(
                    "Email recognised. Please continue."
                );

                this._showVerifiedBadge();
            } else {
                this._showExtraDetails();

                this._setMessage(
                    "We could not match this email. Please provide your contact and company details."
                );

                this._showVerifyButton();
            }

            this._showTicketDetails();
        } catch {
            if (requestNumber !== this._requestNumber) {
                return;
            }

            this._hideExtraDetails();
            this._hideTicketDetails();
            this._showVerifyButton();

            this._setMessage(
                "The email address could not be checked. Please try again."
            );
        } finally {
            if (requestNumber === this._requestNumber) {
                this.verifyButton.disabled = false;
                this.emailInput.disabled = false;
            }
        }
    },

    _onPageShow() {
        this._resetAfterSubmissionIfNeeded();
    },

    _resetAfterSubmissionIfNeeded() {
        let shouldReset = false;

        try {
            shouldReset =
                sessionStorage.getItem(
                    SUBMISSION_RESET_FLAG
                ) === "1";
        } catch {
            /*
             * The verification form can continue to work even when browser
             * storage is unavailable.
             */
            return;
        }

        if (!shouldReset) {
            return;
        }

        sessionStorage.removeItem(
            SUBMISSION_RESET_FLAG
        );

        /*
         * Reset restores server-provided defaults, including a logged-in
         * user's prefilled email, while removing the previous ticket data.
         */
        this.el.reset();

        this._requestNumber += 1;

        this._clearValidationState();
        this._clearMessage();
        this._hideExtraDetails();
        this._hideTicketDetails();
        this._showVerifyButton();

        this.verifyButton.disabled = false;
        this.emailInput.disabled = false;
    },

    _clearValidationState() {
        this.el
            .querySelectorAll(
                ".is-invalid, .is-valid"
            )
            .forEach((element) => {
                element.classList.remove(
                    "is-invalid",
                    "is-valid"
                );
            });

        this.el
            .querySelectorAll(".o_has_error")
            .forEach((element) => {
                element.classList.remove(
                    "o_has_error"
                );
            });

        const formResult = this.el.querySelector(
            "#s_website_form_result"
        );

        if (formResult) {
            formResult.replaceChildren();
        }
    },

    _showTicketDetails() {
        this.ticketDetailsSection.classList.remove(
            "d-none"
        );
    },

    _hideTicketDetails() {
        this.ticketDetailsSection.classList.add(
            "d-none"
        );
    },

    _setMessage(text) {
        this.message.textContent = text;

        this.message.classList.remove(
            "d-none"
        );
    },

    _clearMessage() {
        this.message.textContent = "";

        this.message.classList.add(
            "d-none"
        );
    },

    _hideExtraDetails() {
        this.nameGroup.classList.add(
            "d-none"
        );

        this.companyGroup.classList.add(
            "d-none"
        );

        this.nameInput.required = false;
        this.companyInput.required = false;
    },

    _showExtraDetails() {
        this.nameGroup.classList.remove(
            "d-none"
        );

        this.companyGroup.classList.remove(
            "d-none"
        );

        this.nameInput.required = true;
        this.companyInput.required = true;
    },

    _showVerifiedBadge() {
        this.verifyButton.classList.add(
            "d-none"
        );

        this.verifiedBadge.classList.remove(
            "d-none"
        );
    },

    _showVerifyButton() {
        this.verifyButton.classList.remove(
            "d-none"
        );

        this.verifiedBadge.classList.add(
            "d-none"
        );
    },
});


/*
 * This widget runs on the acknowledgement page after Odoo has successfully
 * created the ticket. It records that the submission form must be cleared if
 * the customer returns using the browser Back button.
 */
publicWidget.registry.AdiHelpdeskSubmissionComplete =
    publicWidget.Widget.extend({

        selector: "body",

        start() {
            const result = this._super(...arguments);

            const path = window.location.pathname.replace(
                /\/+$/,
                ""
            );

            if (
                path.endsWith(
                    "/your-ticket-has-been-submitted"
                )
            ) {
                try {
                    sessionStorage.setItem(
                        SUBMISSION_RESET_FLAG,
                        "1"
                    );
                } catch {
                    /*
                     * Do not disrupt the acknowledgement page if browser
                     * storage is unavailable.
                     */
                }
            }

            return result;
        },
    });