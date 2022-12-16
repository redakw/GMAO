# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api
from openerp import SUPERUSER_ID
from openerp.exceptions import AccessError
from openerp.osv import osv, fields
from openerp.tools import config
from openerp.tools.misc import find_in_path
from openerp.tools.translate import _
from openerp.addons.web.http import request
from openerp.tools.safe_eval import safe_eval as eval

import re
import time
import base64
import logging
import tempfile
import lxml.html
import os
import subprocess
from contextlib import closing
from distutils.version import LooseVersion
from functools import partial
from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.graphics.barcode import createBarcodeDrawing


class Report(osv.Model):
    _inherit = "report"

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None, context=None):
        """This method generates and returns pdf version of a report.
        """
        # dev S
        if report_name == "gmao_alm.incident_template_report":
            for sale in self.pool['cmms.incident'].browse(cr, uid, ids):
                sale.write({
                    'impr': True,
                    'user_impr': uid,
                    'date_impr': fields.datetime.now(),  
                })
        # dev E
        if context is None:
            context = {}

        if html is None:
            html = self.get_html(cr, uid, ids, report_name, data=data, context=context)

        html = html.decode('utf-8')  # Ensure the current document is utf-8 encoded.

        # Get the ir.actions.report.xml record we are working on.
        report = self._get_report_from_name(cr, uid, report_name)
        # Check if we have to save the report or if we have to get one from the db.
        save_in_attachment = self._check_attachment_use(cr, uid, ids, report)
        # Get the paperformat associated to the report, otherwise fallback on the company one.
        if not report.paperformat_id:
            user = self.pool['res.users'].browse(cr, uid, uid)
            paperformat = user.company_id.paperformat_id
        else:
            paperformat = report.paperformat_id

        # Preparing the minimal html pages
        css = ''  # Will contain local css
        headerhtml = []
        contenthtml = []
        footerhtml = []
        irconfig_obj = self.pool['ir.config_parameter']
        base_url = irconfig_obj.get_param(cr, SUPERUSER_ID, 'report.url') or irconfig_obj.get_param(cr, SUPERUSER_ID, 'web.base.url')

        # Minimal page renderer
        view_obj = self.pool['ir.ui.view']
        render_minimal = partial(view_obj.render, cr, uid, 'report.minimal_layout', context=context)

        # The received html report must be simplified. We convert it in a xml tree
        # in order to extract headers, bodies and footers.
        try:
            root = lxml.html.fromstring(html)
            match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

            for node in root.xpath("//html/head/style"):
                css += node.text

            for node in root.xpath(match_klass.format('header')):
                body = lxml.html.tostring(node)
                header = render_minimal(dict(css=css, subst=True, body=body, base_url=base_url))
                headerhtml.append(header)

            for node in root.xpath(match_klass.format('footer')):
                body = lxml.html.tostring(node)
                footer = render_minimal(dict(css=css, subst=True, body=body, base_url=base_url))
                footerhtml.append(footer)

            for node in root.xpath(match_klass.format('page')):
                # Previously, we marked some reports to be saved in attachment via their ids, so we
                # must set a relation between report ids and report's content. We use the QWeb
                # branding in order to do so: searching after a node having a data-oe-model
                # attribute with the value of the current report model and read its oe-id attribute
                if ids and len(ids) == 1:
                    reportid = ids[0]
                else:
                    oemodelnode = node.find(".//*[@data-oe-model='%s']" % report.model)
                    if oemodelnode is not None:
                        reportid = oemodelnode.get('data-oe-id')
                        if reportid:
                            reportid = int(reportid)
                    else:
                        reportid = False

                # Extract the body
                body = lxml.html.tostring(node)
                reportcontent = render_minimal(dict(css=css, subst=False, body=body, base_url=base_url))

                contenthtml.append(tuple([reportid, reportcontent]))

        except lxml.etree.XMLSyntaxError:
            contenthtml = []
            contenthtml.append(html)
            save_in_attachment = {}  # Don't save this potentially malformed document

        # Get paperformat arguments set in the root html tag. They are prioritized over
        # paperformat-record arguments.
        specific_paperformat_args = {}
        for attribute in root.items():
            if attribute[0].startswith('data-report-'):
                specific_paperformat_args[attribute[0]] = attribute[1]

        # Run wkhtmltopdf process
        return self._run_wkhtmltopdf(
            cr, uid, headerhtml, footerhtml, contenthtml, context.get('landscape'),
            paperformat, specific_paperformat_args, save_in_attachment
        )