{
    "name": "ADI Helpdesk Custom",
    "version": "17.0.1.0.0",
    "summary": "ADI customisations for Odoo Helpdesk",
    "author": "Paul Davies - ADI",
    "category": "Helpdesk",
    "depends": [
        "helpdesk",
        "sale_management",
        "stock",
        "adi_contacts_custom",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/software_version_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/set_in_progress_wizard_views.xml",
        "views/review_validity_wizard_views.xml",
        "views/helpdesk_blocklist_views.xml",
        "views/confirm_email_block_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "adi_helpdesk_custom/static/src/scss/helpdesk_ticket.scss",
            "adi_helpdesk_custom/static/src/js/helpdesk_ticket_problem_toggle.js",
        ],
        "web.assets_frontend": [
            "adi_helpdesk_custom/static/src/js/website_form_message.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}