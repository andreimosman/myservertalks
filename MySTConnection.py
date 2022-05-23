#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
   This file is part of MyServerTalks.

    MyServerTalks is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    MyServerTalks is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MyServerTalks; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''
import xmpp, os, sys, locale
from MySTParser import *
from MySTContactManager import *
from MySTFormatReply import *

'''
 TODO:
  - Throw specific exception insted Exception
  - Use config file to indicate if sasl and tls are requirements
'''
class MySTConnection:

	def __init__(self, module_manager):
		self.user = ''
		self.password = ''
		self.server = ''
		self.parser = MySTParser()
		self.module_manager = module_manager
		self.roster = None
	
	# Connect to jabber
	def connect(self, user, password):
		
		# set the user and pass for atributes
		self.user     = user
		self.password = password
		
		self.jid = xmpp.JID(self.user)
		self.user, self.server, self.password = self.jid.getNode(), self.jid.getDomain(), self.password
		
		# Enable all debug flags
		debug_flags = ['nodebuilder', 'dispatcher', 'gen_auth', 'SASL_auth', 'bind', 'socket', 'CONNECTproxy', 'TLS', 'roster', 'browser', 'ibb']
		self.jabber = xmpp.Client(self.server, debug=[])
		
		# Try connect to jabber
		self.conn = self.jabber.connect()
		
		if not self.conn:
			print 'Unable to connect to server %s!' % self.server
			sys.exit(1)

		self.auth = self.jabber.auth(self.user, self.password)
		
		# Check if user is authenticated
		if not self.auth:
			print 'Unable to authorize on %s - check login/password.' % self.server
			sys.exit(1)
		
		# Check if SASL it's possible
		if self.auth != 'sasl':
			print 'Warning: Unable to perform SASL auth os %s. Old authentication method used!' % self.server
			
		self.jabber.RegisterHandler('message', self.messageHandler)
		self.jabber.RegisterHandler('presence', self.presenceHandler)
		self.jabber.sendInitPresence()

		self.roster = self.jabber.getRoster()
		
		self.module_manager.getUserHandler().setContactHandler(MySTContactManager(self.roster))
		
	# Disconnect from jabber
	def disconnect(self):
		self.jabber.disconnected()
		
	def presenceHandler(self, conn, presence):
		source = presence.getFrom()
		try:
			contact, resource = source.__str__().split('/')
		except Exception:
			contact, resource = source.__str__(), ''
		
		# When get user status "unavailable" the system cleans user environment
		if (presence.getType() == 'unavailable'):
			self.module_manager.getUserHandler().cleanUserEnvironment(contact)
			return
		
		if presence.getErrorCode():
			return
		
		escope = self.module_manager.getUserHandler().getUserEscope(contact)
		if (escope == 'user'):
			show   = 'dnd'
			status = 'Do Not Disturb'
		elif (escope == 'super'):
			show   = 'avail'
			status = 'Available'
		else:
			# If the user has no escope set-up him as invalid
			#newPresence = xmpp.Presence(to=source)
			#newPresence.setType('unavailable')
			#self.jabber.send(newPresence)       
			#return
			return

		newPresence = xmpp.Presence(to=source, show=show, priority=5, status=status)
		self.jabber.send(newPresence)
		
	# Send a message
	def messageSend(self, to, message):
		# get the default local language and encoding
		language, encoding = locale.getdefaultlocale()
		# decode the message
		message = message.decode(encoding)
		# send the message
		self.jabber.send(xmpp.Message(to, message))
		
	# Message handler for received messages
	def messageHandler(self, conn, mess):
		text = mess.getBody()
		instruct = MySTParser.parse(text)
		if instruct == None:
			return
		
		# Get the contact sending the message
		contact, resource = mess.getFrom().__str__().split('/')
		
		# Set contact
		instruct.setContact(contact)
		
		# Set the escope
		instruct.setEscope(self.module_manager.getUserHandler().getUserEscope(contact));
		
		# Reply to contact
		reply = self.module_manager.execute(instruct)
		
		# Format to send the reply
		output_format = self.module_manager.getUserHandler().getUserEnvironment('display')
		
		# Get the output format
		output = MySTFormatReply.getOutput(output_format, reply)
		if (output.strip() != ''):
			presence = xmpp.Presence()
			presence.setFrom(mess.getFrom())
			self.presenceHandler(conn, presence)
			# Send the reply
			self.messageSend(mess.getFrom(), output)

	# Loop for process and connection status check
	def loop(self):
		while True:
			try:
				# Check if is connected, if not try reconnect
				if not (self.jabber.isConnected()):
					print 'Disconnected... Trying to reconnect now...\n'
					self.connect(self.user, self.password)

				self.jabber.Process(1)
			except KeyboardInterrupt: 
				break

