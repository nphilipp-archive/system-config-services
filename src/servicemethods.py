"""The servicemethods module handles all the backend processesing for the redhat-config-services application."""
# serviceactions.py
# Copyright (C) 2002 Red Hat, Inc.
# Author: Tim Powers <timp@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import string
import re
import os
import sys
from translate import _, N_, cat


def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    import os
    text=""
    pipe = os.popen('{ ' + cmd + '; } 2>&1', 'r')
    try:
        text = pipe.read()
    except IOError,v:
        text = pipe.read()
        
    sts = pipe.close()
    if sts is None: sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts, text

class ServiceMethods:
    """Includes methods used to find services, and information about them such
    as the description, whether or not it is configured etc."""
        
    def __init__(self):
        self.UNKNOWN=0
        self.RUNNING=1
        self.STOPPED=2
        
    def get_status(self,servicename):
        status = self.UNKNOWN
        try:
            message = getstatusoutput("LANG=C /sbin/service " + servicename + " status < /dev/null")[1]
        except:
            return (self.UNKNOWN,"")

        if string.find(message,"running")!=-1:
            status=self.RUNNING
        if string.find(message,"stopped")!=-1:
            status=self.STOPPED
        return (status,message)
        
    def get_descriptions(self, service_script):
        """Gets the description for the given initscript or xinet.d script"""
        formatted_description = ""
        for i in range(0, len(service_script)):

            if (string.find("%s" % service_script[i], "description:") != -1 ):
                service_script[i] = string.replace(service_script[i], "description:" ,"")

                while (string.find("%s" % service_script[i], "\\") != -1) :
                    service_script[i] = string.replace(service_script[i], "#", "")
                    service_script[i] = string.replace(service_script[i], "\\", "\n")
                    service_script[i] = string.strip(service_script[i])
                    formatted_description = formatted_description + " " + service_script[i]
                    i = i + 1

                formatted_description = formatted_description + " " + string.strip(string.replace(service_script[i],"#",""))
                
        return formatted_description



    def check_if_chkconfiged(self, service_list):
       """Makes sure that these are initscripts recognized by chkconfig, if they
       aren't chkconfig compatible we remove them from the list"""
       services = []
       for servicename in service_list:
	    if servicename[-1:] == '~' or servicename[-1:] == ',' or \
	      servicename[-8:] == '.rpmsave' or servicename[-7:] == '.rpmnew' or \
	      servicename[-4:] == '.swp' or servicename[-8:] == '.rpmorig':
		  continue
	    configured_list = getstatusoutput("LANG=C /sbin/chkconfig --list " + servicename)
	    if configured_list[0] != 0:
		continue
	    services.append(servicename)
       return services

    def check_if_on(self, servicename, editing_runlevel):
        """returns 0 if the service is not configured, and 1 if it is"""
        #runlevel = self.get_runlevel()
        dirlist = os.listdir("/etc/rc.d/rc%s" % editing_runlevel + ".d")

        have_match = -1

        while have_match == -1:
            #for i in range(0,len(dirlist)):
            for direntry in dirlist:
                # check for start links only, we don't care if there is a kill link
                if re.match(r'^[S][0-9][0-9]' + servicename, direntry ):
                    have_match = 1
                    break
            # no match    
            if have_match != 1:
               have_match = 0
               
        return have_match



    def xinetd_check_if_on(self,servicename):
        """returns 0 if the xinetd service is not enabled, 1 if it is enabled, and 1 if
        there is no disabled line"""
        try:
            f = open("/etc/xinetd.d/" + servicename)
        except IOError, msg:
            print "/etc/xinetd.d/" + servicename, msg
            sys.exit(1)
            
        xinetdscript = f.readlines()
        f.close()
        isenabled = 1
        
        for i in range(0,len(xinetdscript)):
            if (string.find(xinetdscript[i], "disable")) != -1:
                
                if (string.find(xinetdscript[i], "yes")) != -1:
                    isenabled = 0
                    break

        return isenabled
                         
        

    def get_runlevel(self):
        """returns the current runlevel, uses /sbin/runlevel"""
        runlevel_output = getstatusoutput("/sbin/runlevel")
        # This is the current runlevel
        return runlevel_output[len(runlevel_output)-1][2]



    def chkconfig_add_del(self, servicename, add_or_del, editing_runlevel):
        """calls chkconfig --level , on if add_or_del == 1, off if add_or_del == 0"""
        if add_or_del == 1:
            chkconfig_action = "on"
        elif add_or_del == 0:
            chkconfig_action = "off"

        if add_or_del == 1 or add_or_del == 0:
            try:
                getstatusoutput("LANG=C /sbin/chkconfig --level %s %s %s" % (editing_runlevel, servicename, chkconfig_action))
            except IOError:
                pass
            self.dict_services[servicename][0][int(editing_runlevel)] = add_or_del
            
        return self.dict_services



    def xinet_add_del(self, xinetd_servicename, add_or_del):
        """adds and removes 'disable = yes' from xinetd service scripts"""
        if add_or_del == 1:
            disable_option = "on"
        elif add_or_del == 0:
            disable_option = "off"

        if add_or_del == 1 or add_or_del == 0:
            try:
                getstatusoutput("LANG=C /sbin/chkconfig %s %s" % (xinetd_servicename , disable_option))
            except:
                pass
            # for xinetd services, set the dictionary to show that it's disabled in all runlevels
            for i in range(0,7):
                self.dict_services[xinetd_servicename][0][i] = add_or_del

        return self.dict_services

            
                
    def get_service_list(self, editing_runlevel, idle_func):
        """populates the self.dict_services, self.dict_services_orig dictionaries and the self.allservices list with service information including whether or not a service is configured to start in runlevels 0-6, as well as whether it is an xinetd service, as well as service descriptions."""
        self.dict_services= {}
        # this will be an unmodified self.dict_services
        self.dict_services_orig = {}

        
        idle_func ()
        list_xinetd_services = self.check_if_chkconfiged(os.listdir("/etc/xinetd.d"))
        idle_func ()
        self.allservices = []
        
        chkconfig_list = getstatusoutput("LANG=C /sbin/chkconfig --list")[1]
        chkconfig_list = re.split('\n', chkconfig_list)
        dict={}
        for i in chkconfig_list:
            x=re.split(r"\t", i.strip())
            name=x[0].strip().split(":")[0]
            if name != "xinetd based services":
                runlevel=x[1:]
                if len(runlevel) > 1:
                    for i in xrange(0,len(runlevel)):
                        runlevel[i]=runlevel[i].split(":")[1]
                dict[name]=runlevel

        for servicename in dict.keys():
            if len(dict[servicename]) == 1:
                continue
            idle_func ()
            # read each initscript
            initscript = []
            try:
                f = open("/etc/init.d/" + servicename)
            except IOError, msg:
                print "/etc/init.d/" + servicename , msg
                raise
                
            line = f.readline()
            while line:
                if re.match('\A\#', line):
                    initscript.append(line)
                    line = f.readline()
                else:
                    f.close()
                    break
                
            runlevels = dict[servicename]
            for i in range(0, len(runlevels)):
                runlevels[i] = string.strip(runlevels[i])
                if runlevels[i] == "off" :
                    runlevels[i] = 0
                else:
                    runlevels[i] = 1
            # configured = 1 if configured already
            # configured = self.check_if_on(servicename, editing_runlevel)

            self.dict_services[servicename] = [runlevels, 0, self.get_descriptions(initscript)]
            self.dict_services_orig[servicename] = [runlevels, 0]
            
            # look through the first 25 lines to see if we have "hide: true" in there.
            # if it's there, remove the service from the dictionary
            for i in range(0, len(initscript)):
                if (string.find("%s" % initscript[i], "hide:") != -1) and \
                   (string.find("%s" % initscript[i], "true") != -1):
                    del self.dict_services[servicename]
                    del self.dict_services_orig[servicename]
                
        for servicename in list_xinetd_services:
            # read each file for xinetd.d
            try:
                f = open("/etc/xinetd.d/%s" % servicename)
            except IOError, msg:
                print "/etc/xinetd.d/" + servicename, msg
                sys.exit(1)
                
            xinetd_script = f.readlines()
            f.close()

            runlevels = dict[servicename]

            if runlevels[0] == "off":
                del runlevels[0]
                for i in range(0,7):
                    runlevels.append(0)
            elif runlevels[0] == "on":
                del runlevels[0]
                for i in range(0,7):
                    runlevels.append(1)
            else:
                continue

            # configured=1 if the service is configured already
            # configured = self.xinetd_check_if_on(servicename)
            
            # the list corresponding to the key is: [configured, is it an xinetd serv., description]
            self.dict_services[servicename] = [runlevels, 1, "%s" % self.get_descriptions(xinetd_script) + _("\n\nYou must enable xinetd to use this service.")]
            self.dict_services_orig[servicename] = [runlevels, 1]
            
        self.allservices = self.dict_services.keys()
        self.allservices.sort()

        # an unmodified dictionary. Needed to compare for saving etc.
                
        return self.allservices , self.dict_services



    def save_changes(self, servicename, service_enabled, editing_runlevel):
        """when this method is used it saves the change to disk"""
        if self.dict_services[servicename]:
            # only save changes
            if int(self.dict_services_orig[servicename][0][int(editing_runlevel)]) != int(service_enabled):
                self.dict_services[servicename][0][int(editing_runlevel)] = service_enabled
                
                #check to make sure we are an initscript and not an xinetd service
                if int(self.dict_services[servicename][1]) == 0:
                    # if it's toggled on
                    if self.dict_services[servicename][0][int(editing_runlevel)] == "1":
                        self.chkconfig_add_del(servicename, 1, editing_runlevel)
                    # if it's toggled off
                    elif self.dict_services[servicename][0][int(editing_runlevel)] == "0":
                        self.chkconfig_add_del(servicename, 0, editing_runlevel)
                # for xinetd services
                elif int(self.dict_services[servicename][1]) == 1:
                    # if it's toggled on
                    if self.dict_services[servicename][0][int(editing_runlevel)] == "1":
                        self.xinet_add_del(servicename, 1)
                    # if it's toggled off
                    elif self.dict_services[servicename][0][int(editing_runlevel)] == "0":
                        self.xinet_add_del(servicename, 0)



    def service_action_results(self, servicename, action_type, runlevel):
        """starts, stops, and restarts the service. returns the error if the service failed in any of the actions"""
        if self.dict_services.has_key(servicename):
            if int(self.dict_services[servicename][1]) == 1:
                if int(self.dict_services["xinetd"][0][int(runlevel)]) == 1:
                    action_results = getstatusoutput("/sbin/service xinetd reload < /dev/null ")

                    if action_results[0] != 0:
                        return (1,_("xinetd failed to reload for ") + servicename +
                                _(". The error was: ") + action_results[1])
                    else:
                        return (0,_("xinetd reloaded %s successfully"))

                else:
                    return (1, _("xinetd must be enabled for %s to run") % servicename)

            if int(self.dict_services[servicename][1]) == 0:
                action_results = getstatusoutput("/sbin/service %s %s < /dev/null" % (servicename, action_type))
                if action_results[0] != 0:
                    return (1, _("%s failed. The error was: %s") % (servicename,action_results[1]))
                else:
                    return (0,"%s %s" % (servicename, action_type) + _(" successful"))
                
