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
from MySTBase import *
from MySTModuleCore import *
from MySTModuleExternal import *
from MySTModuleInterface import *
from MySTReply import *

class MySTModuleManager:
	
	def __init__(self, config, user_handler):

		# Module cache
		self._MOD_COMM = {}
		self._MOD_CALL = {}
		self._MOD_SCOP = {}
		
		self.user_handler = user_handler
		self.config       = config
		
		# Get the modules list
		self.modules = self.config.get('modules')
		
		# Handlers
		self.core      = MySTModuleCore(self.config, self.user_handler)
		self.external  = MySTModuleExternal(self.config)
		self.interface = MySTModuleInterface()

		# mod_core is to cache core reserved functions (that is allways present and cannot be overriden)
		self._MOD_CORE = self.core.getCoreFunctions()

		self.loadConfigInfo()

	# Get user
	def getUserHandler(self):
		return self.user_handler
		
	def getEscope(self, command):
		try:
			return self._MOD_SCOP[command]
		except Exception:
			return ''
	
	def getType(self, command):
		try:
			return self._MOD_COMM[command]
		except Exception:
			return ''

	def getCall(self, command):
		try:
			return self._MOD_CALL[command]
		except Exception:
			return ''

	def execute(self, instruct):
		type   = self.getType(instruct.getCommand())
		escope = self.getEscope(instruct.getCommand())
		
		# User enabled validation
		if not self.user_handler.isUserEnabled(instruct.getContact()):
			return MySTReply(MySTBase.getErrorCode(), 'Error. User not enabled.')
		
		# Escope validatons
		escope_ok = False
		try:
			escope.index(self.user_handler.getUserEscope(instruct.getContact())).__str__()
			escope_ok = True
		except Exception:
			pass
		
		# TODO:
		# - Verify if the user can run this command
		if escope_ok:
			if (type == 'core' or type == 'internal'):
				return self.core.execute(instruct)
			elif (type == 'external'):
				return self.external.execute(instruct)
			elif (type == 'interface'):
				return self.interface.execute(instruct)

		return MySTReply(MySTBase.getErrorCode(), MySTBase.getCommandNotFoundMessage())
		

	def loadConfigInfo(self):
		# Cache Core Functions
		for m in self._MOD_CORE:
			self._MOD_COMM[m] = 'core'
			self._MOD_SCOP[m] = self._MOD_CORE[m]
		# Walk for modules list
		for m in self.modules:
			if not self._MOD_CORE.has_key(m):
				if self.modules[m].has_key('status'):
					if (self.modules[m]['status'].lower() == 'enabled'):
						# cache informations about this enabled module
						if self.modules[m].has_key('type'):
							if self.modules[m].has_key('call'):
								if (self.modules[m]['type'].lower() == 'external'):
									self._MOD_CALL[m] = self.modules[m]['call']
								else:
									self._MOD_CALL[m] = '';

								self._MOD_COMM[m] = self.modules[m]['type'].lower()

								if self.modules[m].has_key('escope'):
									self._MOD_SCOP[m] = self.modules[m]['escope'].lower().split(',')
								
