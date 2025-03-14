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
		self.desktop_cron_file="/etc/cron.d/lliurex-shutdowner-thinclients"
		self.override_shutdown_folder="/etc/lliurex-shutdowner"
		self.override_shutdown_token=os.path.join(self.override_shutdown_folder,"client-override_shutdown.token")
		self.adi_client="/usr/bin/natfree-client"

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
		
		self.core.register_variable_trigger("SHUTDOWNER","ShutdownerClient",self.shutdowner_trigger)
		
		# Making sure we're able to read SHUTDOWNER var from server
		tries=10
		for x in range(0,tries):
		
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
		
		override_shutdown=False
		override_shutdown_enabled=self._is_override_shutdown_enabled()

		if value!=None:
			if not value["cron_values"]["server_shutdown"]:
				if override_shutdown_enabled:
					override_shutdown=True

			if not override_shutdown:
				if value["cron_enabled"]:
					if value["cron_content"]!=None:
						value["cron_content"]=value["cron_content"].replace("&gt;&gt;",">>")
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

	def is_shutdown_override_shutdown_enabled(self):

		is_enabled=self._is_override_shutdown_enabled()
		
		return n4d.responses.build_successful_call_response(is_enabled)

	#def is_shutdown_override_shutdown_enabled

	def enable_override_shutdown_shutdown(self):

		value=self.core.get_variable("SHUTDOWNER")["return"]
		ret=False
		if not value["cron_values"]["server_shutdown"]:
			self._create_override_shutdown_token()
			self._delete_cron_file()
			ret=True
		
		return n4d.responses.build_successful_call_response(ret)

	#def enable_override_shutdown_shutdown

	def disable_override_shutdown_shutdown(self):

		self._delete_override_shutdown_token()
		value=self.core.get_variable("SHUTDOWNER")["return"]

		if value!=None:
			if value["cron_enabled"]:
				if value["cron_content"]!=None:
					value["cron_content"]=value["cron_content"].replace("&gt;&gt;",">>")

					self._create_cron_file(value)

		return n4d.responses.build_successful_call_response()

	#def disable_override_shutdown_shutdown

	def _is_override_shutdown_enabled(self):

		if not os.path.exists(self.override_shutdown_folder):
			return False
		else:
			if os.path.exists(self.override_shutdown_token):
				return True
			else:
				return False

	#def _is_override_shutdown_enabled 

	def _create_cron_file(self,value):

		f=open(self.cron_file,"w")
		f.write(value["cron_content"])
		f.close()

	#def _create_cron_file

	def _delete_cron_file(self):

		if os.path.exists(self.cron_file):
			os.remove(self.cron_file)

	#def _delete_cron_file

	def _create_override_shutdown_token(self):

		if not os.path.exists(self.override_shutdown_folder):
			os.mkdir(self.override_shutdown_folder)

		if not os.path.exists(self.override_shutdown_token):
			f=open(self.override_shutdown_token,'w')
			f.close()

	#def _create_override_shutdown_token

	def _delete_override_shutdown_token(self):

		if os.path.exists(self.override_shutdown_token):
			os.remove(self.override_shutdown_token)

	#def _delete_override_shutdown_token
	
	def _is_client_mode(self):

		is_client=False
		is_desktop=False
	
		try:
			cmd='lliurex-version -v'
			p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
			result=p.communicate()[0]

			if type(result) is bytes:
				result=result.decode()

			flavours = [ x.strip() for x in result.split(',') ]

			for item in flavours:
				if 'server' in item:
					is_client=False
					break
				elif 'client' in item:
					is_client=True
				elif 'desktop' in item:
					is_desktop=True
					if os.path.exists(self.adi_client):
						is_client=True
			
			if is_client:
				if is_desktop:
					if not self._check_connection_with_server():
						is_client=False
			
			return is_client
			
		except Exception as e:
			return False
	
	#def _is_client_mode

	def _check_connection_with_server(self):

		try:
			context=ssl._create_unverified_context()
			client=n4dclient.ServerProxy('https://server:9779',context=context,allow_none=True)
			test=client.is_cron_enabled('','ShutdownerManager')
			return True
		except Exception as e:
			return False

	#def _check_connection_with_server

#class ShutdownerClient
