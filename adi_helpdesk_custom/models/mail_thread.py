from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_route(
        self,
        message,
        message_dict,
        model=None,
        thread_id=None,
        custom_values=None,
    ):
        """
        Prevent external recipients of an incoming email from being
        carried onto an internal Helpdesk reply.

        Odoo parses To / Cc addresses into message_dict['partner_ids'].
        _message_route_process() later restores those partners onto the
        new mail.message.

        For an incoming reply from an internal Odoo user to an existing
        Helpdesk ticket, retain only recipients who are themselves
        active internal Odoo users.

        This prevents a customer address from becoming an explicit
        recipient of an internal Helpdesk Note.
        """

        routes = super().message_route(
            message,
            message_dict,
            model=model,
            thread_id=thread_id,
            custom_values=custom_values,
        )

        # Only affect replies routed to an EXISTING Helpdesk ticket.
        is_existing_helpdesk_reply = any(
            route_model == "helpdesk.ticket" and route_thread_id
            for (
                route_model,
                route_thread_id,
                _route_custom_values,
                _route_user_id,
                _route_alias,
            ) in routes
        )

        if not is_existing_helpdesk_reply:
            return routes

        # message_route() has now resolved author_id.
        author_id = message_dict.get("author_id")

        if not author_id:
            return routes

        author = self.env["res.partner"].sudo().browse(
            author_id
        ).exists()

        if not author:
            return routes

        author_is_internal = bool(
            author.user_ids.filtered(
                lambda user:
                    user.active
                    and not user.share
            )
        )

        if not author_is_internal:
            return routes

        # Incoming mail from an internal Odoo user:
        # do not allow external To / Cc partners to be restored as
        # explicit recipients of the resulting internal Helpdesk Note.
        parsed_partner_ids = message_dict.get(
            "partner_ids",
            [],
        )

        if parsed_partner_ids:
            partners = self.env["res.partner"].sudo().browse(
                parsed_partner_ids
            ).exists()

            internal_partners = partners.filtered(
                lambda partner:
                    bool(
                        partner.user_ids.filtered(
                            lambda user:
                                user.active
                                and not user.share
                        )
                    )
            )

            message_dict["partner_ids"] = internal_partners.ids

        return routes