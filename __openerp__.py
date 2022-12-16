
{
    'name': 'gmao',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'sequence': 2,
    'summary': 'Leads, Opportunities, Phone Calls',
    'description': """
The generic OpenERP Customer Relationship Management
====================================================

This application enables a group of people to intelligently and efficiently manage leads, opportunities, meetings and phone calls.

It manages key tasks such as communication, identification, prioritization, assignment, resolution and notification.

OpenERP ensures that all cases are successfully tracked by users, customers and suppliers. It can automatically send reminders, escalate the request, trigger specific methods and many other actions based on your own enterprise rules.

The greatest thing about this system is that users don't need to do anything special. The CRM module has an email gateway for the synchronization interface between mails and OpenERP. That way, users can just send emails to the request tracker.

OpenERP will take care of thanking them for their message, automatically routing it to the appropriate staff and make sure all future correspondence gets to the right place.


Dashboard for CRM will include:
-------------------------------
* Planned Revenue by Stage and User (graph)
* Opportunities by Stage (graph)
""",
    'author': 'OpenERP SA',
    'website': 'https://www.odoo.com/page/crm',
    'depends': [
        'base',
         'cmms'
    ],
    'data': [
	'views/cmms_views.xml',
    'report/fiche_vie_report.xml',
    'report/fiche_vie_template_report.xml',
    'report/incident_report.xml',
    'report/incident_template_report.xml',
    'report/incident_template_report1.xml',

    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
