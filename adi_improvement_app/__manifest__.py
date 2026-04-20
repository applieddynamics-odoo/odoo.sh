# -*- coding: utf-8 -*-
{
    "name": "ADI Improvement App",
    "license": "LGPL-3",
    "summary": "Management of Corrective Actions (CAR) and Continuous Improvements (CI)",
    "description": "Management of Corrective Actions (CAR) and Continuous Improvements (CI)",
    "author": "Paul Davies",
    "category": "ADI Custom Modules",
    "version": "17.0.1.0.0",
    "depends": ["base", "sale", "mail", "web", "hr"],
    "data": [
        "security/adi_improvement_app_groups.xml",
        "security/ir.model.access.csv",
        "data/mail_activity_type.xml",
        "data/sequences.xml",
        "data/assets.xml",
        "views/views.xml",
        "views/car_wizard_views.xml",
        "views/roles_responsibility_views.xml",
        'views/mail_activity_schedule_views.xml',
    ],
    "assets": {
        "web.assets_web": [
            "adi_improvement_app/static/src/scss/adi_improvement_app.scss",
            "adi_improvement_app/static/src/js/asset_test.js",
        ],
    },
    "installable": True,
    "application": True,
}
