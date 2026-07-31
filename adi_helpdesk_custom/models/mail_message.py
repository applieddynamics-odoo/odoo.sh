from odoo import models


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _portal_message_format(self, properties_names, options=None):
        values_list = super()._portal_message_format(
            properties_names,
            options=options,
        )

        for message, values in zip(self, values_list):
            author = message.author_id

            internal_author = False
            if author:
                author_sudo = author.sudo()

                is_helpdesk_identity = (
                    (author_sudo.email_normalized or "").lower()
                    == "helpdesk@support.adi.com"
                )

                has_internal_user = any(
                    not user.share
                    for user in author_sudo.user_ids
                )

                internal_author = (
                    is_helpdesk_identity
                    or has_internal_user
                )

            body = str(message.body or "")

            values.update({
                "adi_is_internal_author": (
                    message.model == "helpdesk.ticket"
                    and internal_author
                ),

                "adi_body_already_green": (
                    "Support Rating Invitation Sent" in body
                ),
            })

        return values_list