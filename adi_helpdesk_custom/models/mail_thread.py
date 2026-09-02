from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _mail_find_partner_from_emails(
        self,
        emails,
        records=None,
        force_create=False,
        extra_domain=False,
    ):
        """
        Prevent Odoo Helpdesk inbound email processing from
        auto-creating Contacts for unknown senders.

        Existing Contacts may still be matched normally.
        """

        if self.env.context.get(
            "adi_helpdesk_no_partner_autocreate"
        ):
            force_create = False

        return super()._mail_find_partner_from_emails(
            emails,
            records=records,
            force_create=force_create,
            extra_domain=extra_domain,
        )