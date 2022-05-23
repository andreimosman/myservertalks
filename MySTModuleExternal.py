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
import sys, os, popen2
from MySTBase import *
from MySTLog import *
from MySTReply import *

class MySTModuleExternal:
	
	def __init__(self, config):
		self.config = config
	
	def execute(self, instruct):
		# get the command
		extension = instruct.getCommand().lower()
		try:
			# File to call
			file = self.config.get('modules', extension, 'call')
			
			# normalize path separators
			fullpath = os.path.normpath(MySTBase.getExternalExtensionDir()+file)
			
			# Verify if file exists
			if (file == '' or not os.path.exists(fullpath)):
				raise Exception()
			
			# Add commas to path for directories with spaces
			fullpath = '"' + fullpath + '"'
			
			# Execute the command
			r, w, e = popen2.popen3(fullpath + ' ' + instruct.__str__())
			
			# Read the output
			output = "\n".join(r.readlines())
			
			# Close all
			r.close()
			w.close()
			e.close()
			
			# log the executed command
			MySTLog.log('External extension ' + extension + ' called, executing ' + file)
		except:
			output = MySTBase.getCommandNotFoundMessage();
		
		# call the reply object
		return MySTReply(MySTBase.getSucessCode(), output)
