# -*- coding: utf-8 -*-
 

from openerp import models, fields, api, _

from dateutil.relativedelta import *
import time
from datetime import timedelta 
from openerp.exceptions import Warning
import datetime 
 
from openerp import tools
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#ajouter des champs au niveau de OT
class champsOT(models.Model):
	_inherit = 'cmms.incident'

	#creation de l'OT Maintenance preventive <==> Bon Travail

	# intervenant = fields.Char()
	
	ot_regl =fields.Boolean('OT réglementaire',readonly=True)
	nature_mc= fields.Selection([('mc','MC'), ('action_mp','action MP')], 'Nature de OT')
	affectation_incident = fields.Selection([('a_Errahali','a.Errahali'),('l_Chamouti','l.Chamouti'),(' m_Belkarime',' m.Belkarime'),('m_Elghour','m.Elghour'),('n_Arrabhy','n.Arrabhy')],'Affectation')
	line_id_incident= fields.Many2one('cmms.line', 'Ligne de Production',readonly=False)
	user2_id=fields.Many2one('res.users', 'Intervenant',required=True,readonly=True)
	activ = fields.Boolean('Active',compute="change_actv")
	activ2 = fields.Boolean('Active',default=True,compute="change_actv")
	cmms_interc_id= fields.Many2one('cmms.cm','Maintenance Corrective')
	Ref_mp= fields.Char('Maintenance Preventive')
	cmms_interp_id= fields.Many2one('cmms.pm','Maintenance Preventive')
	answers_ids_pm= fields.One2many('cmms.answer.history','ot_idp_pm','Questions')
	# answers_ids= fields.One2many(related='cmms_interp_id.answers_ids')					
	# answers_ids_incident= fields.One2many(related='cmms_interp_id.answers_ids_pm') #True related
	answers_ids_incident= fields.One2many('cmms.answer.history','ot_idp_incident','Questions') 
	panier_ot= fields.One2many('cmms.panier','incident_panier','panier') 
    
	failure_incident=fields.Many2one('cmms.failure','Panne',readonly=True)
    
	meters = fields.Selection([('days', 'Days'),
								 ('h', 'Hebdomadaire'),
								 ('m', 'mensuel'),
								 ('t', 'Trimestriel'),
								 ('s', 'semestriel'),
								 ('a', 'Annuel'),
								 ('2ans', '2ans'),
								 ('5ans', '5ans')], 'Unite de Mesure',readonly=True)
	days_next_due2= fields.Datetime(string='Prochaine Date',required=True,readonly=True)
	type_maintenance_origin= fields.Char(string='Type Maintenance')
	statut_2 = fields.Selection([('lancer', 'Lancer'),('cloturer', 'Cloturer')], 'Statut',default='lancer',readonly=True)
	realisation_date=fields.Datetime(readonly=True)
	action_global= fields.Integer(readonly=True)
	action= fields.Integer()
	duree= fields.Float()
	duree_realiser= fields.Float()
	type_maintenance = fields.Char(String='Type Maintenance')
	maintenance = fields.Char(String='Ref Maintenance')
	# sm = fields.Char()
	# sm = fields.Char(compute='semaine')
	sm_new = fields.Integer()
	year = fields.Integer()
	month = fields.Integer()
	# datetime.datetime(year,month,day).isocalendar()[1]
	date_r= fields.Datetime(string='Date Realisation',readonly=True)
	diagnosistab_ids= fields.One2many('cmms.diagnosistab','mot_id','Quest')
	failure_id=fields.Many2one('cmms.failure','Panne',readonly=True)
	attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel',  'record_relation_id', 'attachment_id', string="Attachments")
	perioT= fields.Many2one('cmms.table','periodicite')
	checklist_id_incident = fields.Many2one('cmms.checklist', 'Checklist')
	description_panne_incident = fields.Text('Description de panne',readonly=True)
	impr =fields.Boolean('impr')
	date_impr= fields.Datetime(string='Date impr')
	user_impr = fields.Many2one('res.users', 'impr par')
	duree_realiser_prev= fields.Float(compute='total_duree_fiche_vie', store=True) 
	duree_prevue_prev= fields.Float(compute='total_duree_fiche_vie', store=True)
	duree_realiser_corr= fields.Float(compute='total_duree_fiche_vie_corr', store=True)
	# answers_ids_incident= fields.One2many('cmms.answer.history','ot_idp_incident','Questions')
	duree_prevue_prev_mep= fields.Float(compute='mep', store=True )
	duree_prevue_prev_aht= fields.Float(compute='aht', store=True )	
	organe=fields.Many2one('cmms.organe','Organes')
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement',readonly=False)
	confirmation = fields.Selection([('confirmer', 'Confirmer')],readonly=True)


	@api.one
	@api.depends('answers_ids_incident')
	def mep(self):

		duree_ht = 0
		for line in self.answers_ids_incident:
			if line.etat == 'mep':
				duree_ht += line.duree 
		self.duree_prevue_prev_mep = duree_ht

	@api.one
	@api.depends('answers_ids_incident','answers_ids_incident.duree')
	def aht(self):

		duree_mep = 0
		for line in self.answers_ids_incident:
			if line.etat != 'mep':
				duree_mep += line.duree 
		self.duree_prevue_prev_aht = duree_mep
        
        
	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		if 'sm_new' in fields:
			fields.remove('sm_new')
		return super(champsOT, self).read_group( domain, fields, groupby, offset=0, limit=limit, orderby=orderby, lazy=lazy)
 
 
	@api.one
	@api.depends('answers_ids_incident','answers_ids_incident.duree_realiser')
	def total_duree_fiche_vie(self):
 
		duree_r = 0
		for line in self.answers_ids_incident:
			duree_r += line.duree_realiser
		self.duree_realiser_prev = duree_r

		duree_p = 0
		for line in self.answers_ids_incident:
			duree_p += line.duree
		self.duree_prevue_prev = duree_p
		
	@api.one
	@api.depends('diagnosistab_ids','diagnosistab_ids.Duree')
	def total_duree_fiche_vie_corr(self):
 
		duree_r = 0
		for line in self.diagnosistab_ids:
			duree_r += line.Duree
		self.duree_realiser_corr = duree_r
    #OT <==> Fiche de Vie
	@api.one
	def change_actv(self):	 

		for question in self.answers_ids_incident:
			
			if question.statut_ok == 'nonok' or question.statut_ok == '':
				self.activ=False
			else:
				self.activ2=True
		for question in self.answers_ids_incident:				
			if question.statut_ok == 'ok':
				self.activ=True
			else:
				self.activ2= False
			
	# @api.multi
	# def action_done(self):
			# return super(champsOT, self).action_done()
			
	@api.multi
	def action_done(self):

		if not self.diagnosistab_ids and not self.Ref_mp:
                    raise Warning(_('Vous devez remplir l action'))
		if not self.attch_ids and self.ot_regl== True:
                    raise Warning(_('Merci de joindre le fichier necessaire'))
		action = 0
		duree = 0
		duree_realiser = 0
		c=''
		n=''
		self.intervenant= ""
		self.date_r= datetime.datetime.now()
		self.statut_2= 'cloturer'
		otcf=self.env['cmms.fiche_vie']
		dates = []

		if (self.ref and self.ref._name == 'cmms.cm') or (self.cmms_interc_id):
			for line in self.diagnosistab_ids:
				duree += line.Duree

		elif (self.ref and self.ref._name == 'cmms.pm') or (self.Ref_mp):
			for line in self.answers_ids_incident:
			
				if line.duree_realiser== 0:
					raise Warning(_('Merci de saisir la durée realiser'))
					
					
				if line.etat_ref != 0 :
					if line.mesure == 0  :
						raise Warning(_('la valeur de mesure est invalable'))
						
					if line.etat_ref < line.mesure and line.etat_ref_max == 0 :
						raise Warning(_('la valeur de mesure est invalable'))

				if line.etat_ref != 0 and line.etat_ref_max != 0:
					if  line.mesure< line.etat_ref  or line.mesure> line.etat_ref_max :
						raise Warning(_('la valeur de mesure est invalable'))
                             
				action += line.action +1
				duree += line.duree
				duree_realiser += line.duree_realiser
				# ----------remplir le champ statut automatiquement par ok----------
				# if(line.statut_ok != 'ok' and line.statut_ok != 'nonok'):
					# line.statut_ok = 'ok'
				# -------------------
				if(line.statut_ok != 'ok'):
					raise Warning(_('le statut doit être validé '))
				
		#		
		if (self.cmms_interc_id) or (self.ref and self.ref._name == 'cmms.cm'):
			
			c = "Maintenance corrective"
			n= self.cmms_interc_id.name 
			
			# n=  self.ref.name  
	
			# n=  self.cmms_interc_id.name 
			
		elif (self.Ref_mp) or (self.ref and self.ref._name == 'cmms.pm'):
			c = "Maintenance preventive"
			n= self.Ref_mp
			
		# self.write({'duree' : duree})
		self.action = action
		self.duree = duree
		self.duree_realiser = duree_realiser
		self.date_r = self.date_r
		# self.realisation_date = max(d for d in dates)
		self.type_maintenance = c
		self.maintenance = n
		# self.state = 'done'
		return super(champsOT, self).action_done()
		###	
	# @api.one
	# def semaine(self):
		# year = int(self.date.split('-')[0])
		# month = int(self.date.split('-')[1])
		# day = int(self.date.split('-')[2].split(' ')[0])
		# self.sm = datetime.datetime(year,month,day).isocalendar()[1]
		# self.annee=self.days_next_due2.split('-')[0]
	 
	@api.multi
	def pdr_valider(self):

		self.confirmation= 'confirmer'		

	@api.multi
	def unlink(self):
		raise Warning(_('test'))
		
#class Product(models.Model):
    #_inherit = 'product.product'
    # code = fields.Char(string='Code',compute='compute_code')
    #type_article = fields.Selection([('m','M'), ('p','P')],'Type Article')
    #sous_equipment_type_id = fields.Many2one('cmms.sous.equipment.type')
    # @api.one
    # def compute_code(self):
		# self.code =  'org'  +'00' + str(self.id)
	
#ajouter les sous ligne aux machines
class CmmsLine(models.Model):
	_inherit = 'cmms.equipment'
	_order= "nbr_equipment"
	type_machine = fields.Selection([('equipement','Equipement'), ('instrument','Instrument')],'Type Machine', required=True)
	nbr_equipment= fields.Integer('Sequence',required=True)
	ot_regl =fields.Boolean('OT réglementaire')
	"""s_line = self.env['cmms.child.line'].search(['line_id.name', '=', 'L1'])"""
	
	child_line_id= fields.Many2one('cmms.child.line', 'Sous ligne de production',  domain="[('line_id', '=', line_id)]")
	ref= fields.Char(required=True)
	# type = fields.Char(readonly=True, compute='compute_ref')
	
	# @api.one
	# def compute_ref(self):
		# self.ref =  self.line_id.code + '' + self.child_line_id.Ref_sl 

	# @api.multi
	# def unlink(self):
		# if self.intervention_id:
			# raise Warning(_('test'))
		# else:
			# return super(CmmsLine, self).unlink()
	# type = fields.Char(readonly=True, compute='compute_ref')
	# def compute_ref(self):
	
		# self.type =  self.line_id.code + '/' + self.child_line_id.Ref_sl + '/' + '' + str(self.id) + ''

	"""count = fields.Integer(default=0)
	self.count = max(self.count)+1"""

 
class CmmsChildLine(models.Model):
	_name='cmms.child.line'
	
	Ref_sl= fields.Char('Ref Sous Ligne de Production',required=True)
	name= fields.Char('Sous Ligne de Production', size=64, required=True)
	
	emplacement_sl= fields.Integer('Emplacement')
	sequence_sl= fields.Integer('Sequence')
	
	line_id= fields.Many2one('cmms.line', 'ligne de production 333')


class CmmsLine(models.Model):
	_inherit='cmms.line'
	child_line_ids= fields.One2many('cmms.child.line','line_id', 'Sous ligne de production')
			

class MPM(models.Model):
	_inherit='cmms.pm'

	attchment = fields.Many2many('ir.attachment', 'ir_attac','record_relation_id', 'attachment_id')
	count_line_version= fields.Integer('count_line_version', compute='count_line_vers')
	version= fields.Integer('Version')
	affectation_mp = fields.Selection([('a_Errahali','a.Errahali'),('l_Chamouti','l.Chamouti'),(' m_Belkarime',' m.Belkarime'),('m_Elghour','m.Elghour'),('n_Arrabhy','n.Arrabhy')],'Affectation') 
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement') 
	perido_id=fields.Many2one('cmms.table','Periodicite') 
	supp =fields.Boolean('Supp?')
	archiver =fields.Boolean('Archiver')
	# retard =fields.Boolean('retard',compute='mp_retard')
	
	#nom de frs et code frs et Origine mp
	otp_ids= fields.One2many('cmms.incident','cmms_interp_id', 'Bon de travail')
	type_mp = fields.Selection([('frs','Fournisseur'), ('local','en local')],'Type MP')
	fournisseur= fields.Char('Nom Fournisseur', size=64)
	
	code_F= fields.Char('Code Fournisseur', size=64)
	origine_mp= fields.Char('Origine MP', size=64, readonly='1',default='Interne')
	days_interval1= fields.Integer('Interval_mp',readonly=False)
	st= fields.Char()
	emetteur = fields.Many2one('res.users', 'Emetteur')
	test_date= fields.Datetime(string='test_date' )
	line_id_pm= fields.Many2one('cmms.line', 'Ligne de Production')
	line_ids_version= fields.One2many('cmms.version','line_id_mp','Version')
	ot_regl =fields.Boolean('MP réglementaire')
	prev_retard =fields.Boolean(compute='mp_retard')
	
	# attchs = fields.Many2many('ir.attachment', 'ir_attach_rel','record_relation_id', 'attachment_id')
	# attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel',  'record_relation_id', 'attachment_id', string="Attachments")
    
	@api.multi
	def mp_retard(self):
		
		for record in self:
                    if str(datetime.datetime.now()) > record.days_next_due2:
                        record.prev_retard = True
                    else:
                        record.prev_retard = False
                        
	# @api.model
	# def alert_hebdo(self):              
            # msg = MIMEMultipart()
            # server = smtplib.SMTP('smtp.office365.com',587)
            # server.starttls()
            # server.login('noreply@alphagroup.ma','@lpha@2022') 
            # msg['Subject'] = 'Rappel Preventive Gmao' 
            # message = "Lancement du preventive hebdomadaire" 
            # msg.attach(MIMEText(message))          
            # server.sendmail('noreply@alphagroup.ma','T.elhanaoui@alphagroup.ma', msg.as_string()) 
            # server.sendmail('noreply@alphagroup.ma','m.mahjoubi@alphagroup.ma', msg.as_string()) 
            # server.sendmail('noreply@alphagroup.ma','l.sabri@alphagroup.ma', msg.as_string())
            # server.sendmail('noreply@alphagroup.ma','l.chamouti@alphagroup.ma', msg.as_string())
            # server.sendmail('noreply@alphagroup.ma','r.kwyasse@alphagroup.ma', msg.as_string()) 
            # server.quit()                                                       

	@api.model
	def alert_mensuel(self):              
            msg = MIMEMultipart()
            server = smtplib.SMTP('smtp.office365.com',587)
            server.starttls()
            server.login('noreply@alphagroup.ma','@lpha@2022')
            msg['Subject'] = 'Rappel Preventive Gmao' 
            message = "Lancement du preventive Mensuel" 
            msg.attach(MIMEText(message))          
            server.sendmail('noreply@alphagroup.ma','T.elhanaoui@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','m.mahjoubi@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.sabri@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.chamouti@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','r.kwyasse@alphagroup.ma', msg.as_string()) 
            server.quit()


	@api.model
	def alert_trim(self):              
            msg = MIMEMultipart()
            server = smtplib.SMTP('smtp.office365.com',587)
            server.starttls()
            server.login('noreply@alphagroup.ma','@lpha@2022')
            msg['Subject'] = 'Rappel Preventive Gmao' 
            message = "Lancement du preventive Trimestriel" 
            msg.attach(MIMEText(message))          
            server.sendmail('noreply@alphagroup.ma','T.elhanaoui@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','m.mahjoubi@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.sabri@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.chamouti@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','r.kwyasse@alphagroup.ma', msg.as_string())
            server.quit()
 
	@api.model
	def alert_sem(self):              
            msg = MIMEMultipart()
            server = smtplib.SMTP('smtp.office365.com',587)
            server.starttls()
            server.login('noreply@alphagroup.ma','@lpha@2022')
            msg['Subject'] = 'Rappel Preventive Gmao' 
            message = "Lancement du preventive Semestriel" 
            msg.attach(MIMEText(message))          
            server.sendmail('noreply@alphagroup.ma','T.elhanaoui@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','m.mahjoubi@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.sabri@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.chamouti@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','r.kwyasse@alphagroup.ma', msg.as_string())

            server.quit()

	@api.model
	def alert_annuel(self):              
            msg = MIMEMultipart()
            server = smtplib.SMTP('smtp.office365.com',587)
            server.starttls()
            server.login('noreply@alphagroup.ma','@lpha@2022')
            msg['Subject'] = 'Rappel Preventive Gmao' 
            message = "Lancement du preventive Annuel" 
            msg.attach(MIMEText(message))          
            server.sendmail('noreply@alphagroup.ma','T.elhanaoui@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','m.mahjoubi@alphagroup.ma', msg.as_string()) 
            server.sendmail('noreply@alphagroup.ma','l.sabri@alphagroup.ma', msg.as_string()) 
            server.quit()
            
	# @api.multi
	# def mp_retard(self):
		# for record in self:
                    # if str(datetime.datetime.now()) > record.days_next_due2 :
                        # record.retard = True
                    # else:
                        # record.retard =False
                        
	@api.one
	def count_line_vers(self):
		self.count_line_version=len(self.line_ids_version)

 	@api.onchange('meter')
	def vers(self):
		v=1
		v=self.version+1
		self.version=v

 	@api.onchange('line_id_pm')
	def line_prod(self):
		v=1
		v=self.version+1
		self.version=v
		
 	@api.onchange('equipment_id')
	def equip(self):
		v=1
		v=self.version+1
		self.version=v
		
 	@api.onchange('Sous_Equip')
	def sous_equip(self):
		v=1
		v=self.version+1
		self.version=v
		
	# @api.onchange('answers_ids_pm')
	# def modif(self):
			
		# v=1
		# v=self.version+1
		# self.version=v
		
	# @api.one
	# def write(self, vals):
	
		# res = super(MPM, self).write(vals)
		# if self.version != self.count_line_version:
			# raise Warning(_('Veuillez remplir la nature de modification'))       
		
		# return res
        
#-------------------------------button lancement du prochaine preventive 
	# @api.multi
	# def to_bon_travailll(self):
		
		# otp=self.env['cmms.incident']
		# self.days_next_due2= fields.Datetime.to_string(fields.Datetime.from_string(self.days_next_due2)+ timedelta(self.days_interval1))
		# answer_obj = self.env['cmms.answer.history']
		# vals={
			  # 'equipment_id': self.equipment_id.id,
			  # 'Ref_mp': self.name,
			  # 'line_id_incident': self.line_id_pm.id,
			  # 'meters': self.meter,
			  # 'days_next_due2': self.days_next_due2,
			  # 'Sous_Equip': self.Sous_Equip.id,
              # 'type_maintenance_origin': "Maintenance preventive",
			  
		# }
		# new_otp=otp.create(vals)
		# new_otp.cmms_interp_id = self.id

		
		# for answer in self.answers_ids_pm:
			# vals = {
				# 'name': answer.name,
				# 'etat': answer.etat,
				# 'profil': answer.profil,
				# 'pdr': answer.pdr,
				# 'consommables': answer.consommables,
				# 'outillage': answer.outillage,
				# 'etat_reference': answer.etat_reference,
				# 'duree': answer.duree,
				# 'ot_idp_incident': new_otp.id,
			# }
			# new_answerp=answer_obj.create(vals)

#-------------------------------------------------------- 
			# r=new_otp							
			# for answer in motp.answers_ids_pm:
				# answers_ids_incident=r
								
   
			# for answer in line.answers_ids_pm:
				# print("answer", answer.name)
				# answer.ot_idp_incident =new_otp

		# self.days_next_due2= fields.Datetime.to_string(fields.Datetime.from_string(self.days_next_due2)+ timedelta(self.days_interval1))
        # changement du prochaine date du MP apres il la transfere au Prochaine date du OT 
        
	@api.onchange('type_mp')
	def Ofournisseur(self):
	
		if self.type_mp == "frs":
			self.origine_mp ='Externe'	
			
		if self.type_mp == "local":
			self.origine_mp ='Interne'	
			
 	@api.onchange('meter')
	def Interval(self):
		if self.meter == "days":
			self.days_interval1 =1
			
		if self.meter == "h":
			self.days_interval1 =7

		if self.meter == "m":
			self.days_interval1 =30	
			
		if self.meter == "t":
			self.days_interval1 =90
			
		if self.meter == "s":
			self.days_interval1 =180
			
		if self.meter == "a":
			self.days_interval1 =360

		if self.meter == "2ans":
			self.days_interval1 =720

		if self.meter == "5ans":
			self.days_interval1 =1800		
	# @api.multi
	# def unlink(self):
		# if self.supp==True:
		# raise Warning(_('test'))
			
	checklist_id = fields.Many2one('cmms.checklist', 'Checklist')#cmms.checklist.history
	answers_ids_pm= fields.One2many('cmms.answer.history','ot_idp_pm','Questions')
	# checklist_id = fields.Many2one('cmms.checklist', 'Checklist')
	# answers_ids= fields.One2many('cmms.answer.history','ot_idp','Questions')
    
    
	panier_pr= fields.One2many('cmms.panier','ot_idp_pn','panier')

	
	def onchange_checklist_id(self, cr, uid, ids, id, context={}):
		liste = self.pool.get('cmms.question').search(cr, uid, [('checklist_id', '=', id)])
		enrs = self.pool.get('cmms.question').name_get(cr, uid, liste)
		res = []
		for id, name in enrs:
			obj = {'name': name }
			res.append(obj)
		return {'value':{'answers_ids_pm': res}}	

#creation de l'OT Maintenance corrective <==> Bon Travail


class CmmsIncidenct(models.Model):
	_inherit='cmms.cm'
    
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement', required=True)
	tcmms_interc_id= fields.Many2one('cmms.intervention','cm')
	priorite_cm= fields.Selection([('equipement','Equipement'), ('instrument','Instrument')], 'Type Machine')
	nature_mc= fields.Selection([('mc','MC'), ('action_mp','action MP')], 'Nature de OT', required=True)
	totc_ids= fields.One2many('cmms.incident','cmms_interc_id', 'Bon de travail')
	user2_id_corr=fields.Many2one('res.users', 'Intervenant',required=True)
	line_id_cm= fields.Many2one('cmms.line', 'Ligne de Production',required=True)
	active_correction = fields.Boolean('Active')
    

	@api.multi
	def to_bon_travaill(self):
		#creation de l'OT Maintenance corrective <==> Bon Travail
		self.active_correction=True
		totc=self.env['cmms.incident']
		vals={
			  'nature_mc': self.nature_mc,
			  'line_id_incident': self.line_id_cm.id,
			  'equipment_id': self.equipment_id.id,
			  'Sous_Equip': self.Sous_Equip.id,
			  'days_next_due2': self.date,
			  'sm_new': datetime.date.today().strftime("%W"),
			  'year': datetime.date.today().strftime("%Y"),
			  'month': datetime.date.today().strftime("%m"),
			  'failure_incident': self.failure_id.id,
			  'description_panne_incident': self.description_panne_cm,
			  'user2_id': self.user2_id_corr.id,
			  'user_id': self.user_id.id,
			  'priorite_incident': self.priorite_mc,
              'type_maintenance_origin': "Maintenance Corrective",
			  
		}
		tnew_otc=totc.create(vals)
		tnew_otc.cmms_interc_id = self.id  


class tMaintenance_corrective(models.Model):
	_inherit = 'cmms.intervention'
	totc_ids= fields.One2many('cmms.cm','tcmms_interc_id', 'Bon de travail')
	#creation champ panne  et sous equip au niveau du demande d intervention
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement',required=True)
	failure_id=fields.Many2one('cmms.failure','Panne',required=True)
	active_intervention = fields.Boolean('Active')
	line_id_intervention= fields.Many2one('cmms.line', 'Ligne de Production',required=True)
	@api.multi
	def to_bon_travail(self):
		
		self.active_intervention=True
		totc=self.env['cmms.cm']
		vals={
			  'line_id_cm': self.line_id_intervention.id,
			  'equipment_id': self.equipment_id.id,
			  'Sous_Equip': self.Sous_Equip.id,
			  'failure_id': self.failure_id.id,
			  'date': self.date_inter_c,
			  'user_id': self.user_id.id,
			  # 'resp': self.resp,
			  'priorite_mc': self.priorite,
		}
		tnew_otc=totc.create(vals)
		tnew_otc.tcmms_interc_id = self.id
		tnew_otc.to_bon_travaill()
		# import smtplib
		# from email.MIMEMultipart import MIMEMultipart
		# from email.MIMEText import MIMEText

		
		# receivers_email = self.user_target.login  //tjr en commantaire

														 
		# msg = MIMEMultipart()
		# server = smtplib.SMTP('smtp.gmail.com',587)
		# server.starttls()
		
		# server.login('alphagroup.gmao@gmail.com','Gmao123456')

		# msg['Subject'] = 'Intervention GMAO' 
		# message = "Vous avez une intervention cree Par Mr."+str(self.user_id.name)+"\n Equipement: "+str(self.equipment_id.name)+"\n Panne: "+str(self.failure_id.name)+"\n Priorite: "+str(self.priorite)
		# msg.attach(MIMEText(message))          
		# server.sendmail('alphagroup.gmao@gmail.com','F.SAMYH@alphagroup.ma', msg.as_string()) 
 
		# server.quit()
#question	
class question(models.Model):
	_inherit='cmms.checklist'

	equipment_id= fields.Many2one('cmms.equipment', 'Equipement')
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement')	
	meters_question = fields.Selection([('days', 'Days'),
								 ('h', 'Hebdomadaire'),
								 ('m', 'mensuel'),
								 ('t', 'Trimestriel'),
								 ('s', 'semestriel'),
								 ('a', 'Annuel')], 'Unit of measure')
	
	
# deplacement liste des taches vers bon de travail
class answerhistory_bonTravail(models.Model):
	_inherit='cmms.answer.history'
	
	ot_idp_incident= fields.Many2one('cmms.incident', 'Ordre de Travail')
	checklist_id_incident = fields.Many2one('cmms.checklist', 'Checklist')
	answers_ids_incident= fields.One2many('cmms.answer.history','ot_idp_incident','Questions')
	
	
	# def onchange_checklist_id(self, cr, uid, ids, id, context={}):
		# liste = self.pool.get('cmms.question').search(cr, uid, [('checklist_id_incident', '=', id)])
		# enrs = self.pool.get('cmms.question').name_get(cr, uid, liste)
		# res = []
		# for id, name in enrs:
			# obj = {'name': name }
			# res.append(obj)
		# return {'value':{'answers_ids_incident': res}}
		

	ot_idp_pm= fields.Many2one('cmms.pm', 'Maintenance preventive')
	checklist_id = fields.Many2one('cmms.checklist', 'Checklist')
	answers_ids_pm= fields.One2many('cmms.answer.history','ot_idp_pm','Questions')
	
	def onchange_checklist_id(self, cr, uid, ids, id, context={}):
		liste = self.pool.get('cmms.question').search(cr, uid, [('checklist_id', '=', id)])
		enrs = self.pool.get('cmms.question').name_get(cr, uid, liste)
		res = []
		for id, name in enrs:
			obj = {'name': name }
			res.append(obj)
		return {'value':{'answers_ids_pm': res}}
		
		
# deplacement du  tableau de panne corrective(diagnosistab_ids) au niveau d bon travail
class CmmsItdd(models.Model):
	_inherit='cmms.diagnosistab'
	mot_id= fields.Many2one('cmms.incident', 'OT')


#Questions
class Questions(models.Model):
	_inherit='cmms.answer.history'
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement') 
	equipment_id= fields.Many2one('cmms.equipment', 'Equipement')
	meters_question = fields.Selection([('days', 'Days'),
								 ('h', 'Hebdomadaire'),
								 ('m', 'mensuel'),
								 ('t', 'Trimestriel'),
								 ('s', 'semestriel'),
								 ('a', 'Annuel')], 'Unit of measure')
	
#Fiche de vie
class Fiche_Vie(models.Model):
	_inherit = 'cmms.fiche_vie'

	cmms_interc_id= fields.Many2one('cmms.cm','Maintenance Corrective')
	cmms_interp_id= fields.Many2one('cmms.pm','Maintenance Preventive')
	duree= fields.Char()
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement') 
	equipment_id= fields.Many2one('cmms.equipment', 'Equipement')
	observation= fields.Text()
	realisation_date = fields.Char()
	type_maintenance = fields.Char(String='Type Maintenance')
	maintenance = fields.Char(String='Ref Maintenance')
	

# class TableTemLines(models.Model):
	# _inherit='cmms.table.lines'

	# periodicite = fields.Many2one('cmms.table')
	

class Table_Tem(models.Model):
	_inherit = 'cmms.table'

	# table_tem = fields.One2many('cmms.table.lines', 'periodicite')
	preventiv_ids = fields.One2many('cmms.pm','perido_id', 'Preventive')
	conv= fields.One2many('cmms.incident','perioT', 'Bon de travail')
	emetteur= fields.Many2one('res.users','Emetteur')
	
	@api.one
	def valider(self):
		
		otp=self.env['cmms.incident']
		answer_obj = self.env['cmms.answer.history']
		panier_obj = self.env['cmms.panier']
		for line in self.preventiv_ids:
			
			totp = self.env['cmms.pm'].search([('name', '=', line.name)])
			if totp:
				ctr=0
				for li in totp.answers_ids_pm:
					ctr += 1
				days_next_due=fields.Datetime.from_string(line.days_next_due2)

				vals={	
					'days_next_due2': fields.Datetime.to_string(days_next_due + timedelta(totp.days_interval1)),
				
				}				
				
				tnew_otp=totp.write(vals)
			vals={
				'equipment_id': line.equipment_id.id,
				'Sous_Equip': line.Sous_Equip.id,
				'ot_regl': line.ot_regl,
				'sm_new': datetime.date.today().strftime("%W"),
				'year': datetime.date.today().strftime("%Y"),
				'month': datetime.date.today().strftime("%m"),
				'Ref_mp': line.name, 
				'line_id_incident': line.line_id_pm.id, 
				'meters': line.meter,
				'days_next_due2': line.days_next_due2,
				# 'affectation_incident': line.affectation_mp,
				'user2_id': line.emetteur.id,
				'action_global': ctr,
                'type_maintenance_origin': "Maintenance preventive",
                
				
			}
			new_otp=otp.create(vals)
			new_otp.perioT = self.id
			print("new item", new_otp)

			# r=new_otp							
			# for answer in motp.answers_ids_pm:
				# answers_ids_incident=r								
   
			# for answer in line.answers_ids_pm:
				# print("answer", answer.name)
				# answer.ot_idp_incident =new_otp
				
			# totp = self.env['cmms.pm'].search([('name', '=', line.name)])
			
			# if totp:

				# days_next_due=fields.Datetime.from_string(line.days_next_due2)

				# vals={	
					# 'days_next_due2': fields.Datetime.to_string(days_next_due + timedelta(totp.days_interval1)),
				
				# }				
				
				# tnew_otp=totp.write(vals)
                # changement du prochaine date du MP apres il la transfere au Prochaine date du OT

			for answer_panier in line.panier_pr:
			
				vals = {
					'reference': answer_panier.reference,
					'incident_panier': new_otp.id,
				}
				new=panier_obj.create(vals)
                
			for answer in line.answers_ids_pm:
				vals = {
					'name': answer.name,
					'etat': answer.etat,
					'profil': answer.profil,
					'pdr': answer.pdr,
					'etat_ref': answer.etat_ref,
					'etat_ref_max': answer.etat_ref_max,
					'unite': answer.unite,
					'consommables': answer.consommables,
					'outillage': answer.outillage,
					'etat_reference': answer.etat_reference,
					'duree': answer.duree,
					'ot_idp_incident': new_otp.id,
				}
				new_answerp=answer_obj.create(vals)
				

				
		self.preventiv_ids=False	
	
	def check_ref_in_incident(self, ref,meters,days_next_due2):
		incident_id = self.env['cmms.incident'].search(['|', ('ref', '=', ref),'&', ('Ref_mp', '=', ref), '&',('meters', '=', meters), ('days_next_due2', '=', days_next_due2)])
		if incident_id:
			return False
		else:
			return True

	# def delete_old_lines(self):
		# self.env.cr.execute('delete from cmms_table_lines where periodicite=' + str(self.id))

	@api.one
	def generer(self):
		self.preventiv_ids=False
		# self.delete_old_lines()
		
		
		if self.meters == 'days':
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
					# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
						if mp.days_next_due2.split(' ')[0] == self.date.split(' ')[0]: 
						    mp.perido_id=self.id
							# vals = {
								# 'name': mp.name,
								# 'meter': mp.meter,
								# 'equipment_id': mp.equipment_id.id,
								# 'recurrent': mp.recurrent,
								# 'type_mp': mp.type_mp,
								# 'origine_mp': mp.origine_mp,
								# 'days_next_due2': mp.days_next_due2,
								# 'periodicite': self.id
								
							# }
							# self.table_tem.create(vals)
	
							

		if self.meters == 'h':
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
					# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
						year = int(self.date.split('-')[0])
						month = int(self.date.split('-')[1])
						day = int(self.date.split('-')[2].split(' ')[0])
						
						year1 = int(mp.days_next_due2.split('-')[0])
						month1 = int(mp.days_next_due2.split('-')[1])
						day1 = int(mp.days_next_due2.split('-')[2].split(' ')[0])
						
						if datetime.datetime(year,month,day).isocalendar()[1]== datetime.datetime(year1,month1,day1).isocalendar()[1] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()): 
							mp.perido_id=self.id
							# mp.affectation_mp= self.affectation
							mp.emetteur= self.affectation_user
							
							# mp.emetteur= self.emetteur
							# vals = {
								# 'name': mp.name,
								# 'meter': mp.meter,
								# 'equipment_id': mp.equipment_id.id,
								# 'recurrent': mp.recurrent,
								# 'type_mp': mp.type_mp,
								# 'origine_mp': mp.origine_mp,
								# 'days_next_due2': mp.days_next_due2,
								# 'periodicite': self.id
									
							# }
							# self.table_tem.create(vals)
								

		elif self.meters == 'm':
			# import pdb;
			# pdb.set_trace()
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
					# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
						if mp.days_next_due2.split('-')[1] == self.date.split('-')[1] and mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()): 
							mp.perido_id=self.id
							# mp.affectation_mp= self.affectation
							mp.emetteur= self.affectation_user
							# vals = {
								# 'name': mp.name,
								# 'equipment_id': mp.equipment_id.id,
								# 'meter': mp.meter,
								# 'recurrent': mp.recurrent,
								# 'type_mp': mp.type_mp,
								# 'origine_mp': mp.origine_mp,
								# 'days_next_due2': mp.days_next_due2,
								# 'periodicite': self.id
							# }
							# self.table_tem.create(vals)


		elif self.meters == 't':
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			list_months = []
			if self.date.split('-')[1] in ['01', '02', '03']:
				list_months = ['01', '02', '03']
			elif self.date.split('-')[1] in ['04', '05', '06']:
				list_months = ['04', '05', '06']
			elif self.date.split('-')[1] in ['07', '08', '09']:
				list_months = ['07', '08', '09']
			elif self.date.split('-')[1] in ['10', '11', '12']:
				list_months = ['10', '11', '12']
			for mp in mp_ids:
				# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
					if mp.days_next_due2.split('-')[1] in list_months and\
						mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()): 
							mp.perido_id=self.id
							# mp.affectation_mp= self.affectation
							mp.emetteur= self.affectation_user
						# vals = {
							# 'name': mp.name,
							# 'equipment_id': mp.equipment_id.id,
							# 'meter': mp.meter,
							# 'recurrent': mp.recurrent,
							# 'type_mp': mp.type_mp,
							# 'origine_mp': mp.origine_mp,
							# 'days_last_done': mp.days_last_done,
							# 'periodicite': self.id
						# }
						# self.table_tem.create(vals)
		elif self.meters == 's':
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			list_months = []
			if self.date.split('-')[1] in ['01', '02', '03', '04', '05', '06']:
				list_months = ['01', '02', '03', '04', '05', '06']
			elif self.date.split('-')[1] in ['07', '08', '09', '10', '11', '12']:
				list_months = ['07', '08', '09', '10', '11', '12']
			for mp in mp_ids:
				# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
					if mp.days_next_due2.split('-')[1] in list_months and \
						mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()): 
							mp.perido_id=self.id
							# mp.affectation_mp= self.affectation
							mp.emetteur= self.affectation_user
						# vals = {
							# 'name': mp.name,
							# 'equipment_id': mp.equipment_id.id,
							# 'meter': mp.meter,
							# 'recurrent': mp.recurrent,
							# 'type_mp': mp.type_mp,
							# 'origine_mp': mp.origine_mp,
							# 'days_next_due2': mp.days_next_due2,
							# 'days_last_done': mp.days_last_done,
							# 'periodicite': self.id
						# }
						# self.table_tem.create(vals)
						
						
		elif self.meters == 'a':
			
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
					# if self.check_ref_in_incident(mp.name,mp.meter,mp.days_next_due2) is True:
						
						# if mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()):  
						if  mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()):
							mp.perido_id=self.id
							# mp.affectation_mp= self.affectation
							mp.emetteur= self.affectation_user
 
		elif self.meters == '2ans':
			
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
						
						# dateincrimente= fields.Datetime.to_string(datetime.datetime.now() + timedelta(720))
 
						if mp.days_next_due2.split('-')[0] == self.date.split('-')[0] and mp.line_id_pm== self.line_id_periodicite and  mp.days_next_due2 <= str(datetime.datetime.now()):  
							mp.perido_id=self.id
							mp.emetteur= self.affectation_user

		elif self.meters == '5ans':
			
			mp_ids = self.env['cmms.pm'].search([('meter', '=', self.meters)])
			if mp_ids:
				for mp in mp_ids:
						
						dateincrimente= fields.Datetime.to_string(datetime.datetime.now() + timedelta(1800))
 
						if  mp.days_next_due2 <= dateincrimente and dateincrimente >= mp.days_next_due2    and mp.line_id_pm== self.line_id_periodicite:  
							mp.perido_id=self.id
							mp.emetteur= self.affectation_user
                            
	@api.one
	def annuler(self):
		self.preventiv_ids=False
		
		
#stock.move (ajout du champ OT => lancer)
class stock_move(models.Model):
	_inherit = 'stock.move'	
	ot_stock_move= fields.Many2one('cmms.incident', 'Ordre de Travail')
	
	
#stock.history (fichier stock_account/wizard/stock_valuation_history)	
class stock_history(models.Model):
    _inherit = 'stock.history'
    valeur_stock= fields.Float('valeur stock',compute="testing")
    @api.one
    def testing(self):
		
		self.valeur_stock =  self.quantity * self.product_id.standard_price

class panier_h(models.Model):
	_inherit='cmms.panier'
	
	
	reference= fields.Char('Ref panier')	
	etat= fields.Selection([('traite', 'Traité'),('non_traite', 'Non Traité')], 'etat panier')

	incident_panier= fields.Many2one('cmms.incident', 'Ordre de Travail')
	
	panier_ot= fields.One2many('cmms.panier','incident_panier','Questions')


	ot_idp_pn= fields.Many2one('cmms.pm', 'Maintenance preventive')
	panier_pr= fields.One2many('cmms.panier','ot_idp_pn','Questions')
    
class gmao_version(models.Model):
	_inherit='cmms.version'
	

	ref_version= fields.Char('Ref version')																							
	user_id=fields.Many2one('res.users', 'Redacteur',default=lambda self: self.env.user, readonly=True)																						
	intitule= fields.Text('Intitule')																							
	date_creation= fields.Datetime(string='Date creation',readonly=True, default=lambda self: fields.datetime.now())																							
	version= fields.Integer(string='Version',readonly=True)																							
	nature_modif = fields.Selection([('modification','Modification'),('suppression ','Suppression'),('creation','Creation')],'Nature de Modification') 
	line_id_mp= fields.Many2one('cmms.pm', 'Maintenance preventive')
	ref_mp= fields.Char('Ref MP')
	equipment_id= fields.Many2one('cmms.equipment', 'Equipement')
	Sous_Equip=fields.Many2one('cmms.sous.equipment.type','Sous Equipement')