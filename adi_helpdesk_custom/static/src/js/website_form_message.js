/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdiWebsiteFormMessage = publicWidget.Widget.extend({
    selector: ".s_website_form",

    events: {
        "click .s_website_form_send, click button[type='submit'], click input[type='submit']": "_onSubmitClick",
    },

    _onSubmitClick() {
        setTimeout(() => {
            this.el.querySelectorAll("span.text-danger.ml8").forEach((el) => {
                if (el.textContent.trim() === "Please fill in the form correctly.") {
                    el.textContent =
                        "Some information is missing. Please check the highlighted fields and try again.";
                }

                el.style.display = "block";
                el.style.marginTop = "12px";
                el.style.marginLeft = "0";
                el.style.width = "100%";
            });
        }, 200);
    },
});