from odoo import models, tools


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
        Prevent Helpdesk inbound email processing from
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

    def message_route(
        self,
        message,
        message_dict,
        model=None,
        thread_id=None,
        custom_values=None,
    ):
        """
        Route new inbound Helpdesk email according to ADI's
        trusted-contact rules.

        Existing-thread replies are left completely unchanged.

        For NEW mail addressed to the Helpdesk alias:

        - blocked sender/domain:
              discard the email

        - registered customer contact:
              normal Helpdesk ticket

        - active internal Odoo user:
              normal Helpdesk ticket

        - anything else:
              Customer Enquiry instead of Helpdesk ticket
        """

        routes = super().message_route(
            message,
            message_dict,
            model=model,
            thread_id=thread_id,
            custom_values=custom_values,
        )

        if not routes:
            return routes

        # -----------------------------------------------------
        # Sender email
        # -----------------------------------------------------

        sender_addresses = tools.email_split(
            message_dict.get("email_from")
            or message_dict.get("from")
            or ""
        )

        sender_email = (
            sender_addresses[0].strip().lower()
            if sender_addresses
            else False
        )

        if not sender_email or "@" not in sender_email:
            return routes

        sender_domain = sender_email.rsplit("@", 1)[-1]

        # -----------------------------------------------------
        # Process each route returned by standard Odoo.
        #
        # A route is:
        #
        # (
        #     model,
        #     thread_id,
        #     custom_values,
        #     user_id,
        #     alias,
        # )
        # -----------------------------------------------------

        final_routes = []

        for route in routes:
            (
                route_model,
                route_thread_id,
                route_values,
                route_user_id,
                route_alias,
            ) = route

            # -------------------------------------------------
            # Leave everything alone unless this is a NEW
            # Helpdesk ticket route.
            #
            # Existing ticket replies have a thread_id and must
            # continue through Odoo's normal reply handling.
            # -------------------------------------------------

            if (
                route_model != "helpdesk.ticket"
                or route_thread_id
            ):
                final_routes.append(route)
                continue

            # -------------------------------------------------
            # Blocklist
            # -------------------------------------------------

            Blocklist = self.env[
                "adi.helpdesk.blocklist"
            ].sudo()

            blocked_email = Blocklist.search([
                ("block_type", "=", "email"),
                ("value", "=", sender_email),
                ("active", "=", True),
            ], limit=1)

            if blocked_email:
                # Deliberately discard repeat blocked traffic.
                continue

            # -------------------------------------------------
            # Existing Contact
            # -------------------------------------------------

            Partner = self.env["res.partner"].sudo()

            sender_partner = Partner.search([
                ("email", "=ilike", sender_email),
                ("active", "=", True),
                ("is_company", "=", False),
            ], limit=1)

            # -------------------------------------------------
            # Internal ADI/Odoo user.
            #
            # Keep internal mail working normally even though
            # employee Contacts do not need a customer parent.
            # -------------------------------------------------

            internal_user = (
                sender_partner.user_ids.filtered(
                    lambda user:
                        user.active
                        and not user.share
                )
                if sender_partner
                else self.env["res.users"]
            )

            if internal_user:
                final_routes.append(route)
                continue

            # -------------------------------------------------
            # Trusted customer contact.
            #
            # Exact registered email + individual + parent
            # company. No approved-domain field is required.
            # -------------------------------------------------

            trusted_customer = bool(
                sender_partner
                and sender_partner.parent_id
            )

            if trusted_customer:
                final_routes.append(route)
                continue

            # -------------------------------------------------
            # Unknown sender.
            #
            # Divert the NEW route from helpdesk.ticket to the
            # Customer Enquiry holding model.
            #
            # Keep the existing alias/user context. The enquiry
            # model's message_new() deliberately ignores the
            # Helpdesk alias defaults.
            # -------------------------------------------------

            final_routes.append((
                "adi.helpdesk.enquiry",
                False,
                {},
                route_user_id,
                route_alias,
            ))

        return final_routes