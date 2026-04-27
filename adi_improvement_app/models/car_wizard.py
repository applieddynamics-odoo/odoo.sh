# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContainmentWizard(models.TransientModel):
    _name = "adi_improvement_app.containment_wizard"
    _description = "CAR Containment Wizard"

    car_id = fields.Many2one("adi_improvement_app.car", required=True, ondelete="cascade")

    containment = fields.Text()
    cause = fields.Text()
    car_actions = fields.Text()

    verification_plan = fields.Text(string="Verification Plan")
    verification_notes = fields.Text(string="Verification Notes")
    est_verify_end_date = fields.Date(string="Estimated Verification Completion Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        car_id = self.env.context.get("default_car_id")
        if not car_id:
            return res

        car = self.env["adi_improvement_app.car"].browse(car_id)
        if not car.exists():
            return res

        res.update({
            "containment": car.containment or False,
            "cause": car.cause or False,
            "car_actions": car.car_actions or False,
            "verification_plan": car.verification_plan or False,
            "verification_notes": car.verification_notes or False,
            "est_verify_end_date": car.est_verify_end_date or False,
        })
        return res

    def action_proceed_to_verification(self):
        self.ensure_one()
        car = self.car_id

        if car.status != "containment":
            raise ValidationError("Containment can only be completed from 'Containment' status.")

        if self.containment is not False:
            car.containment = self.containment
        if self.cause is not False:
            car.cause = self.cause
        if self.car_actions is not False:
            car.car_actions = self.car_actions
        if self.verification_plan is not False:
            car.verification_plan = self.verification_plan
        if self.verification_notes is not False:
            car.verification_notes = self.verification_notes
        if self.est_verify_end_date is not False:
            car.est_verify_end_date = self.est_verify_end_date

        if not car.car_date_done:
            car.car_date_done = fields.Date.context_today(car)

        car.status = "awaiting_verification"

        car.message_post(
            body="Containment completed by %s on %s. Record moved to Awaiting Verification."
            % (self.env.user.name, fields.Date.context_today(car).strftime("%d %b %Y"))
        )

        return {"type": "ir.actions.act_window_close"}


class VerificationWizard(models.TransientModel):
    _name = "adi_improvement_app.verification_wizard"
    _description = "CAR Verification Wizard"

    car_id = fields.Many2one("adi_improvement_app.car", required=True, ondelete="cascade")

    verification_plan = fields.Text(string="Verification Plan")
    est_verify_end_date = fields.Date(string="Estimated Verification Completion Date")
    verification_notes = fields.Text()

    def action_proceed_to_verification(self):
        self.ensure_one()
        car = self.car_id

        if car.status != "containment":
            raise ValidationError("Verification can only be started from 'Containment'.")

        if self.verification_plan is not False:
            car.verification_plan = self.verification_plan
        if self.est_verify_end_date:
            car.est_verify_end_date = self.est_verify_end_date
        if self.verification_notes is not False:
            car.verification_notes = self.verification_notes

        if not car.car_date_done:
            car.car_date_done = fields.Date.context_today(car)

        car.status = "awaiting_verification"

        car.message_post(
            body="Containment completed by %s on %s. Record moved to Awaiting Verification."
            % (self.env.user.name, fields.Date.context_today(car).strftime("%d %b %Y"))
        )

        return {"type": "ir.actions.act_window_close"}


class CloseWizard(models.TransientModel):
    _name = "adi_improvement_app.close_wizard"
    _description = "CAR Close Wizard"

    car_id = fields.Many2one("adi_improvement_app.car", required=True, ondelete="cascade")
    verification_plan = fields.Text(string="Verification Plan")
    verification_notes = fields.Text(string="Verification Evidence")
    est_verify_end_date = fields.Date(string="Estimated Verification Completion Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        car_id = self.env.context.get("default_car_id")
        if not car_id:
            return res

        car = self.env["adi_improvement_app.car"].browse(car_id)
        if not car.exists():
            return res

        res.update({
            "verification_plan": car.verification_plan or False,
            "verification_notes": car.verification_notes or False,
            "est_verify_end_date": car.est_verify_end_date or False,
        })
        return res

    def action_verification_failed(self):
        self.ensure_one()
        car = self.car_id

        if car.status != "awaiting_verification":
            raise ValidationError("Verification failure can only be recorded from 'Awaiting Verification'.")

        if self.verification_plan is not False:
            car.verification_plan = self.verification_plan
        if self.verification_notes is not False:
            car.verification_notes = self.verification_notes
        if self.est_verify_end_date is not False:
            car.est_verify_end_date = self.est_verify_end_date

        car.status = "containment"
        car.verification_counter += 1
        car.car_date_done = False

        car.message_post(
            body="Verification failed and was recorded by %s on %s. Record returned to Containment."
            % (self.env.user.name, fields.Date.context_today(car).strftime("%d %b %Y"))
        )

        return {"type": "ir.actions.act_window_close"}

    def action_proceed_to_closure(self):
        self.ensure_one()
        car = self.car_id

        if car.status != "awaiting_verification":
            raise ValidationError("CAR can only be closed from 'Awaiting Verification'.")

        if self.verification_plan is not False:
            car.verification_plan = self.verification_plan
        if self.verification_notes is not False:
            car.verification_notes = self.verification_notes
        if self.est_verify_end_date is not False:
            car.est_verify_end_date = self.est_verify_end_date

        car.verified_by = self.env.user
        if not car.date_closed:
            car.date_closed = fields.Date.context_today(car)
        car.status = "closed"

        car.message_post(
            body="Verification passed and CAR was closed by %s on %s."
            % (self.env.user.name, fields.Date.context_today(car).strftime("%d %b %Y"))
        )

        return {"type": "ir.actions.act_window_close"}


class ReopenWizard(models.TransientModel):
    _name = "adi_improvement_app.reopen_wizard"
    _description = "CAR Reopen Confirmation"

    car_id = fields.Many2one("adi_improvement_app.car", required=True, ondelete="cascade")

    def action_confirm_reopen(self):
        self.ensure_one()
        car = self.car_id

        if car.status != "closed":
            raise ValidationError("Only closed CARs can be reopened.")

        car.status = "awaiting_verification"

        car.message_post(
            body="CAR reopened by %s. Status reset to Awaiting Verification."
            % self.env.user.name
        )

        return {"type": "ir.actions.act_window_close"}