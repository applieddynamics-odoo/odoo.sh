# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ci_app_adi(models.Model):
    _name = 'ci_app_adi.ci_app_adi'
    _description = 'ADI CI and CAR App'

    action_type = fields.Selection([("CI", "CI"), ("CAR", "CAR")])

    # Shared
    title = fields.Char()
    action_reference = fields.Char()
    opened_by = fields.Many2one("res.users")
    date_opened = fields.Date()
    status = fields.Selection([("Open",                  "Open"),
                               ("In Progress",           "In Progress"),
                               ("On Hold",               "On Hold"),
                               ("In Progress",           "In Progress"),
                               ("Awaiting Verification", "Awaiting Verification"),
                               ("Done",                  "Done")],
                              default=("Open", "Open"))

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
    ])
    owner = fields.Text()
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
    verified_by = fields.Many2one("res.user")
    verification_notes = fields.Text()
    documents_affected = fields.Text()

    @api.on_create
    def on_create(self):
        pass
