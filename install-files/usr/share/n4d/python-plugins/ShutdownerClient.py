#!/usr/bin/python3
import os
import threading
import time
import n4d.server.core as n4dcore
import n4d.responses



class ShutdownerClient:

	def __init__(self):
		
		self.core=n4dcore.Core.get_core()
		self.cron_file="/etc/cron.d/lliurex-shutdowner"

	#def init
	
	def startup(self,options):
		
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
		
		if value!=None:

			if value["cron_enabled"]:
				if value["cron_content"]!=None:
					f=open(self.cron_file,"w")
					f.write(value["cron_content"])
					f.close()
			else:
				if os.path.exists(self.cron_file):
					os.remove(self.cron_file)
			
			if value["shutdown_signal"] > self.shutdowner_var["shutdown_signal"]:
				self.shutdown()
		
	#def server_trigger
	
	
	def shutdown(self):
		
		os.system('shutdown -h now')
		
	#def shutdownlist
