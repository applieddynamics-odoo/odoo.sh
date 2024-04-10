# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class ci_app_adi(models.Model):
    _name = "ci_app_adi.ci_app_adi"
    _description = "ADI CI and CAR App"
    _rec_name = "action_reference"

    action_type = fields.Selection([("CI", "CI"), ("CAR", "CAR")])

    # Shared
    title = fields.Char(required=True)
    action_reference = fields.Char()
    opened_by = fields.Many2one("res.users", default=lambda self: self.env.user.id)
    date_opened = fields.Date(default=lambda self: datetime.now())
    status = fields.Selection([("Open",                  "Open"),
                               ("In Progress",           "In Progress"),
                               ("On Hold",               "On Hold"),
                               ("Awaiting Verification", "Awaiting Verification"),
                               ("Done",                  "Done")],
                              default=lambda self: "Open")
    previous_status = fields.Char()

    process_area = fields.Selection([
        ("Proposals and Contracts", "Proposals and Contracts"),
        ("Purchasing",              "Purchasing"),
        ("Receiving",               "Receiving"),
        ("Production",              "Production"),
        ("Systems Engineering",     "Systems Engineering"),
        ("Software Engineering",    "Software Engineering"),
        ("Shipping",                "Shipping"),
        ("Calibration",             "Calibration"),
        ("Export Control",          "Export Control"),
        ("Field Applications",      "Field Applications"),
        ("Contract Review",         "Contract Review"),
        ("Human Resources",         "Human Resources"),
        ("Project Management",      "Project Management")
    ], required=True)
    owner = fields.Char()
    summary = fields.Text()
    notes = fields.Text()

    # CI
    # not permissions-based hence different from 'date_closed'
    date_done = fields.Date()
    
    # CAR
    date_due = fields.Date()
    risk = fields.Selection([("Low",    "Low"),
                             ("Medium", "Medium"),
                             ("High",   "High")])
    related_so = fields.Many2one("sale.order")
    immediate_action = fields.Text()
    cause = fields.Text()
    actions = fields.Text()
    future_improvements = fields.Text()

    # TODO: permissions locked fields
    date_closed = fields.Date()
    verified_by = fields.Many2one("res.users")
    verification_notes = fields.Text()
    documents_affected = fields.Text()

    @api.model
    def create(self, vals):
        if vals["action_type"] == "CI":
            vals["action_reference"] = self.env["ir.sequence"].next_by_code("ci.sequence")
        elif vals["action_type"] == "CAR":
            vals["action_reference"] = self.env["ir.sequence"].next_by_code("car.sequence")
        return super(ci_app_adi, self).create(vals)

    def button_set_in_progress(self):
        for r in self:
            r["previous_status"] = r.status
            r["status"] = "In Progress"

    def button_set_awaiting_verification(self):
        for r in self:
            r["previous_status"] = r.status
            r["date_done"] = datetime.now()
            r["status"] = "Awaiting Verification"

    def button_set_done(self):
        for r in self:
            r["previous_status"] = r.status
            r["date_closed"] = datetime.now()
            r["verified_by"] = self.env.user
            r["status"] = "Done"

    def button_set_on_hold(self):
        for r in self:
            r["previous_status"] = r.status
            r["status"] = "On Hold"
            
    def button_undo(self):
        for r in self:
            tmp = r["previous_status"]
            r["previous_status"] = r.status
            r["status"] = tmp

    def button_revert(self):
        for r in self:
            if r.status == "Open":
                pass
            elif r.status == "In Progress":
                r["status"] = "Open"
            elif r.status == "Awaiting Verification":
                r["status"] = "In Progress"
            elif r.status == "Done":
                r["status"] = "Awaiting Verification"
                

