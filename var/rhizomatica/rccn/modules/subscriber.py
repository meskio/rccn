############################################################################
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Subscriber module
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

import sys
sys.path.append("..")
from config import *
import obscvty

class SubscriberException(Exception):
        pass

class Subscriber:

	def get_balance(self, subscriber_number):
		# check if extension if yes add internal_prefix
		if len(subscriber_number) == 5:
			subscriber_number = config['internal_prefix']+subscriber_number

		try:
			cur = db_conn.cursor()
			cur.execute("SELECT balance FROM subscribers WHERE msisdn=%(number)s AND authorized=1", {'number': subscriber_number})
			balance = cur.fetchone()
			if balance != None:
				return balance[0]
			else:
				raise SubscriberException("Error in getting subscriber balance")
		except psycopg2.DatabaseError, e:
			raise SubscriberException('Database error in getting subscriber balance: %s' % e)

	def set_balance(self, subscriber_number, balance):
		# check if extension if yes add internal_prefix
		if len(subscriber_number) == 5:
			subscriber_number = config['internal_prefix']+subscriber_number
		try:
			cur = db_conn.cursor()
			cur.execute("UPDATE subscribers SET balance=%(balance)s WHERE msisdn=%(number)s", {'balance': Decimal(str(balance)), 'number': subscriber_number})
			db_conn.commit()
		except psycopg2.DatabaseError, e:
			raise SubscriberException('Database error updating balance: %s' % e)


	def is_authorized(self,subscriber_number,auth_type):
		# auth type 0 check subscriber without checking extension
		# auth type 1 check subscriber with checking extension
		try:
			cur = db_conn.cursor()
			
			if auth_type == 1:
				# check if extension if yes add internal_prefix used to find the subscriber by the extension
				if len(subscriber_number) == 5:
					subscriber_number = config['internal_prefix']+subscriber_number

			cur.execute("SELECT msisdn FROM subscribers WHERE msisdn=%(number)s AND authorized=1", {'number': subscriber_number})
			sub = cur.fetchone()
			if sub != None:
				return True
			else:
				return False
		except psycopg2.DatabaseError, e:
			raise SubscriberException('Database error in checking subscriber authorization: %s' % e)

	def get_all(self):
		try:
			cur = db_conn.cursor()
			cur.execute('SELECT * FROM subscribers')
			if cur.rowcount > 0:
				sub = cur.fetchall()
				return sub
			else:
				raise SubscriberException('PG_HLR No subscribers found')
		except psycopg2.DatabaseError, e:
			raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
	

	def get_all_connected(self):
                try:
                        sq_hlr = sqlite3.connect(sq_hlr_path)
                        sq_hlr_cursor = sq_hlr.cursor()
                        sq_hlr_cursor.execute("select extension from subscriber where extension like ? and lac > 0", [(config['internal_prefix']+'%')])
                        connected = sq_hlr_cursor.fetchall()
                        if connected == []:
                                raise SubscriberException('No connected subscribers found')
			else:
				sq_hlr.close()
				return connected

                except sqlite3.Error as e:
                        raise SubscriberException('SQ_HLR error: %s' % e.args[0])
			sq_hlr.close()


	def get(self, msisdn):
		try:
			cur = db_conn.cursor()
			cur.execute('SELECT * FROM subscribers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
			if cur.rowcount > 0:
				sub = cur.fetchone()
				return sub
			else:
				raise SubscriberException('PG_HLR No subscriber found')
		except psycopg2.DatabaseError, e:
			raise SubscriberException('PG_HLR error getting subscriber: %s' % e)


                                              
	def add(self, msisdn, name, balance):
		# check if the subscriber exists in the HLR
                try:
                        sq_hlr = sqlite3.connect(sq_hlr_path)
                        sq_hlr_cursor = sq_hlr.cursor()
			sq_hlr_cursor.execute('select extension from subscriber where extension=?', [(msisdn)])
			extension = sq_hlr_cursor.fetchone()
			if  extension == None:
				raise SubscriberException('Extension not found in the HLR')
			
                except sqlite3.Error as e:
                        raise SubscriberException('SQ_HLR error: %s' % e.args[0])

		# update subscriber data in the sqlite HLR
		#try:
		#	subscriber_number = config['internal_prefix']+msisdn
		#	sq_hlr_cursor.execute('UPDATE Subscriber set extension=?,name=?,authorized=1 where extension=?', (subscriber_number, name, extension[0]))
		#	sq_hlr.commit()
		#except sqlite3.Error as e:
		#	raise SubscriberException('SQ_HLR error updating subscriber data: %s' % e.args[0])
		#finally:
		#	sq_hlr.close()
		subscriber_number = config['internal_prefix']+msisdn
		appstring = "OpenBSC"
		appport = 4242
		vty = obscvty.VTYInteract(appstring, "127.0.0.1", appport)
		cmd = 'enable'
		vty.command(cmd)
		cmd = 'subscriber extension %s extension %s' % (msisdn,subscriber_number)
		vty.command(cmd)
		cmd = 'subscriber extension %s authorized 1' % subscriber_number
		vty.command(cmd)
		cmd = 'subscriber extension %s name %s' % (subscriber_number,name)
		vty.command(cmd)
			
		# provision the subscriber in the database
		try:
			cur = db_conn.cursor()
			cur.execute('INSERT INTO subscribers(msisdn,name,authorized,balance) VALUES(%(msisdn)s,%(name)s,1,%(balance)s)', {'msisdn': subscriber_number, 'name': name, 'balance': Decimal(str(balance))})
			db_conn.commit()
                except psycopg2.DatabaseError, e:
                        raise SubscriberException('PG_HLR error provisioning the subscriber: %s' % e)
			

	def delete(self,msisdn):
		# delete subscriber on the HLR sqlite DB
		#try:
                #       sq_hlr = sqlite3.connect(sq_hlr_path)
                #        sq_hlr_cursor = sq_hlr.cursor()
                #        sq_hlr_cursor.execute('DELETE FROM subscriber WHERE extension=?', [(msisdn)])
		#	if sq_hlr_cursor.rowcount > 0:
		#		sq_hlr.commit()
		#	else:
		#		raise SubscriberException('SQ_HLR No subscriber found')
                #except sqlite3.Error as e:
                #       raise SubscriberException('SQ_HLR error deleting subscriber: %s' % e.args[0])
		#finally:
		#	sq_hlr.close()
                subscriber_number = msisdn[-5:]
                appstring = "OpenBSC"
                appport = 4242
                vty = obscvty.VTYInteract(appstring, "127.0.0.1", appport)
                cmd = 'enable'
                vty.command(cmd)
                cmd = 'subscriber extension %s extension %s' % (msisdn,subscriber_number)
                vty.command(cmd)


		# PG_HLR delete subscriber 
		try:
			cur = db_conn.cursor()
			cur.execute('DELETE FROM subscribers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
			if cur.rowcount > 0:
				db_conn.commit()
			else:
				raise SubscriberException('PG_HLR No subscriber found')	
                except psycopg2.DatabaseError, e:
                        raise SubscriberException('PG_HLR error deleting subscriber: %s' % e)


	def authorized(self,msisdn,auth):
		# auth 0 subscriber disabled
		# auth 1 subscriber enabled 
		# disable/enable subscriber on the HLR sqlite DB
		try:
			sq_hlr = sqlite3.connect(sq_hlr_path)
			sq_hlr_cursor = sq_hlr.cursor()
			sq_hlr_cursor.execute('UPDATE Subscriber SET authorized=? WHERE extension=?', (auth,msisdn))
			if sq_hlr_cursor.rowcount > 0:
				sq_hlr.commit()
			else:
				raise SubscriberException('SQ_HLR Subscriber not found')
		except sqlite3.Error as e:
			raise SubscriberException('SQ_HLR error changing auth status: %s' % e.args[0])
		finally:
			sq_hlr.close()

		# disable/enable subscriber on PG_HLR
		try:
			cur = db_conn.cursor()
			cur.execute('UPDATE subscribers SET authorized=%(auth)s WHERE msisdn=%(msisdn)s', {'auth': auth, 'msisdn': msisdn})
			if cur.rowcount > 0:
				db_conn.commit()
			else:
				raise SubscriberException('PG_HLR Subscriber not found')
		except psycopg2.DatabaseError, e:
			raise SubscriberException('PG_HLR error changing auth status: %s' % e)
			

	def edit(self,msisdn,name,balance):
		# edit subscriber data in the SQ_HLR
		#try:
                #        sq_hlr = sqlite3.connect(sq_hlr_path)
                #        sq_hlr_cursor = sq_hlr.cursor()
		#	sq_hlr_cursor.execute('UPDATE Subscriber set extension=?,name=? where extension=?', (msisdn, name, msisdn))
		#	if sq_hlr_cursor.rowcount > 0:
		#		sq_hlr.commit()
		#	else:
		#		raise SubscriberException('SQ_HLR No subscriber found')
		#except sqlite3.Error as e:
		#	raise SubscriberException('SQ_HLR error updating subscriber data: %s' % e.args[0])
		#finally:
		#	sq_hlr.close()

		# PG_HLR update subscriber data
		try:
			cur = db_conn.cursor()
			if balance != "":
				cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s,balance=%(balance)s WHERE msisdn=%(msisdn2)s', {'msisdn': msisdn, 'name': name, 'balance': Decimal(str(balance)), 'msisdn2': msisdn})
			else:
				cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s WHERE msisdn=%(msisdn2)s', {'msisdn': msisdn, 'name': name, 'msisdn2': msisdn})
			if cur.rowcount > 0:
				db_conn.commit()
			else:
				raise SubscriberException('PG_HLR No subscriber found')	
                except psycopg2.DatabaseError, e:
                        raise SubscriberException('PG_HLR error updating subscriber data: %s' % e)

			


if __name__ == '__main__':
	sub = Subscriber()
	#sub.set_balance('68820110010',3.86)
	try:
		sub.add('20133','Keyla',0)
		#sub.edit('68820137511','Antanz_edit',3.86)
		#sub.authorized('68820137511',0)
		#print sub.get_all_connected()
		
		#a = sub.get('68820137511')
		#print a
		#sub.delete('68820137511')
	except SubscriberException, e:
		print "Error: %s" % e
