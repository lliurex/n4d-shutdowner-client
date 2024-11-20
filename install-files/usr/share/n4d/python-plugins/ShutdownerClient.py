#!/usr/bin/python3
import os
import subprocess
import threading
import time
import n4d.server.core as n4dcore
import n4d.responses
import xmlrpc.client as n4dclient
import ssl

class ShutdownerClient:

	def __init__(self):
		
		self.core=n4dcore.Core.get_core()
		self.cron_file="/etc/cron.d/lliurex-shutdowner"
		self.desktop_cron_file="/etc/cron.d/lliurex-shutdowner-desktop"
		self.override_folder="/etc/lliurex-shutdowner"
		self.override_token=os.path.join(self.override_folder,"client-override.token")

	#def init
	
	def startup(self,options):
		
		if self._is_client_mode():
			if os.path.exists(self.desktop_cron_file):
				os.remove(self.desktop_cron_file)
			t=threading.Thread(target=self._startup)
			t.daemon=True
			t.start()
		
		
	#def startup
	
	def _startup(self):
		
		#Old n4d: objects["VariablesManager"].register_trigger("SHUTDOWNER","ShutdownerClient",self.shutdowner_trigger)
		self.core.register_variable_trigger("SHUTDOWNER","ShutdownerClient",self.shutdowner_trigger)
		
		
		# Making sure we're able to read SHUTDOWNER var from server
		tries=10
		for x in range(0,tries):
		
			#Old n4d:self.shutdowner_var=objects["VariablesManager"].get_variable("SHUTDOWNER")
			self.shutdowner_var=self.core.get_variable("SHUTDOWNER")["return"]
			
			if self.shutdowner_var != None:
				self.shutdowner_trigger(self.shutdowner_var)
				break
			else:
				time.sleep(1)
				
		if self.shutdowner_var == None:
			self.shutdowner_var={}
			self.shutdowner_var["shutdown_signal"]=0


	#def startup
	
	def shutdowner_trigger(self,value):
		
		override=False
		override_enabled=self._is_override_enabled()

		if value!=None:
			if not value["cron_values"]["server_shutdown"]:
				if override_enabled:
					override=True

			if not override:
				if value["cron_enabled"]:
					if value["cron_content"]!=None:
						self._create_cron_file(value)
				else:
					self._delete_cron_file()
				
				if value["shutdown_signal"] > self.shutdowner_var["shutdown_signal"]:
					self.shutdown()
			else:
				self._delete_cron_file()
		
	#def shutdowner_trigger
	
	def shutdown(self):
		
		os.system('shutdown -h now')
		
	#def shutdown

	def is_shutdown_override_enabled(self):

		is_enabled=self._is_override_enabled()
		return n4d.responses.build_successful_call_response(is_enabled)

	#def is_shutdown_override_enabled

	def enable_override_shutdown(self):

		value=self.core.get_variable("SHUTDOWNER")["return"]
		ret=False
		if not value["cron_values"]["server_shutdown"]:
			self._create_override_token()
			self._delete_cron_file()
			ret=True
		
		return n4d.responses.build_successful_call_response(ret)

	#def enable_override_shutdown

	def disable_override_shutdown(self):

		self._delete_override_token()
		value=self.core.get_variable("SHUTDOWNER")["return"]

		if value!=None:
			if value["cron_enabled"]:
				if value["cron_content"]!=None:
					self._create_cron_file(value)

		return n4d.responses.build_successful_call_response()

	#def disable_override_shutdown

	def _is_override_enabled(self):

		if not os.path.exists(self.override_folder):
			return False
		else:
			if os.path.exists(self.override_token):
				return True
			else:
				return False

	#def _is_override_enabled 

	def _create_cron_file(self,value):

		f=open(self.cron_file,"w")
		f.write(value["cron_content"])
		f.close()

	#def _create_cron_file

	def _delete_cron_file(self):

		if os.path.exists(self.cron_file):
			os.remove(self.cron_file)

	#def _delete_cron_file

	def _create_override_token(self):

		if not os.path.exists(self.override_folder):
			os.mkdir(self.override_folder)

		if not os.path.exists(self.override_token):
			f=open(self.override_token,'w')
			f.close()

	#def _create_override_token

	def _delete_override_token(self):

		if os.path.exists(self.override_token):
			os.remove(self.override_token)

	#def _delete_override_token
	
	def _is_client_mode(self):

		isClient=False
		isDesktop=True
	
		try:
			cmd='lliurex-version -v'
			p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
			result=p.communicate()[0]

			if type(result) is bytes:
				result=result.decode()

			flavours = [ x.strip() for x in result.split(',') ]

			for item in flavours:
				if 'adi' in item:
					isDesktop=False
					break

			if isDesktop:
				if self._check_connection_with_adi():
					isClient=True
			
			return isClient
			
		except Exception as e:
			return False
	
	#def _is_client_mode

	def _check_connection_with_adi(self):

		try:
			context=ssl._create_unverified_context()
			client=n4dclient.ServerProxy('https://server:9779',context=context,allow_none=True)
			test=client.is_cron_enabled('','ShutdownerManager')
			return True
		except Exception as e:
			return False

	#def _check_connection_with_adi

