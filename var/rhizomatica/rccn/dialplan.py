############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Dialplan call routing
# This file is part of RCCN
#
# RCCN is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RCCN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from config import *
from context import Context

class Dialplan:

	def __init__(self,session):
		self.session = session

		self.destination_number = self.session.getVariable('destination_number')
		self.calling_number = self.session.getVariable('caller_id_number')

		self.subscriber = Subscriber()
		self.numbering = Numbering()
		self.billing = Billing()
		self.configuration = Configuration()		

		modules = [self.subscriber,self.numbering,self.billing, self.configuration]

		self.context = Context(session,modules)

	def play_announcement(self,ann):
		self.session.answer()
		self.session.execute('playback','%s' % ann)
		self.session.hangup()
		
	def auth_context(self,mycontext):
		# check if the subscriber is authorized to make calls before sending the call to the context
		log.debug('Check if subscriber %s is registered and authorized' % self.calling_number)
		try:
			if self.subscriber.is_authorized(self.calling_number,0):
				log.debug('Subscriber is registered and authorized to call')
				exectx = getattr(self.context, mycontext)
				exectx()
			else:
				self.session.setVariable('context', mycontext.upper())
				log.info('Subscriber is not registered or authorized to call')
				# subscriber not authorized to call
				self.play_announcement('002_saldo_insuficiente.gsm')
		except SubscriberException as e:
			log.error(e)
			# play announcement error
			self.play_announcement('002_saldo_insuficiente.gsm')


	def lookup(self):
		# the processing is async we need a variable
		processed = 0

		# check if destination number is an incoming call
		# lookup dest number in DID table.
		try:
			if (self.numbering.is_number_did(self.destination_number)):
				log.info('Called number is a DID')
				log.debug('Execute context INBOUND call')
				processed = 1
				# send call to IVR execute context
				self.session.setVariable('inbound_loop','0')
				self.context.inbound()
		except NumberingException as e:
			log.error(e)

		# check if destination number is an international call. prefix with + or 00
		if (self.destination_number[0] == '+' or (re.search(r'^00',self.destination_number) != None)) and processed == 0:
			log.debug('Called number is an international call or national')
			# national or international call
			# lookup if it's trying to call another site number
			#if (self.numbering.is_number_site(self.destination_number)):
			#	log.debug('Called number is a local number send call to LOCAL context')
				# yes send call to the right context
			#	processed = 1
			#	self.auth_context('local')
			#else:
				# external call send number outside
			processed = 1
			log.debug('Called number is an external number send call to OUTBOUND context')
			self.auth_context('outbound')

		if processed == 0:
			log.info('Check if called number is local')
			try:
				num_res = self.numbering.is_number_local(self.destination_number)
				if num_res == 0 and len(self.destination_number) == 11:
					log.info('Called number is a local number send call to LOCAL context')
					# yes send call locally
					processed = 1
					self.auth_context('local')
                                elif num_res == 1:
                                        # number is internal
                                        processed = 1
                                        self.auth_context('internal')
				else:
                                        # check if called number is an extension
                                        log.debug('Check if called number is an extension')
                                        if self.destination_number in extensions_list:
						processed = 1
                                                log.info('Called number is an extension, execute extension handler')
                                                self.session.setVariable('context','EXTEN')
                                                extension = importlib.import_module('extensions.ext_'+self.destination_number, 'extensions')
                                                try:
                                                        log.debug('Exec handler')
                                                        extension.handler(self.session)
                                                except ExtensionException as e:
                                                        log.error(e)
					else:
					# check if it's calling a local full number for another site
					# get postcode, send enum request where to send the call
					#log.debug('Check if called number is a full number for another site')
					#if self.numbering.is_number_internal(self.destination_number) == False and len(self.destination_number) == 11:
					#	log.info('Called number is a full number for another site send call to INTERNAL context')
					#	processed = 1
					#	self.auth_context('internal')
					#else:
						# the number called must be wrong play announcement wrong number
						# it's calling an outside number
						# set the caller id (db get) send call to the SIP trunk
						log.info('Wrong number, play announcement of invalid number format')
						processed = 1
						self.play_announcement('007_el_numero_no_es_corecto.gsm')
			except NumberingException as e:
				log.error(e)
