#!/usr/bin/python
""" system-config-services: This module contains the Gui() class which contains the methods pertaining to the gui only """
# serviceconf.py
# Copyright (C) 2002 Red Hat, Inc.
# Authors: Tim Powers <timp@redhat.com>
#          Bill Nottingham <notting@redhat.com>
#          Dan Walsh <dwalsh@redhat.com>
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

import signal
import sys

try:
    import gtk
except RuntimeError,e:
    print "Unable to initialize graphical environment. Most likely cause of failure"
    print "is that the tool was not run using a graphical environment. Please either"
    print "start your graphical user interface or set your DISPLAY variable."
    print "Caught exception: %s" % e
    sys.exit(-1)

domain = "system-config-services"

appPath="/usr/share/%s" % domain
if not appPath in sys.path:
    sys.path.append(appPath)

rhplPath="/usr/lib/python%d.%d/site-packages/rhpl" % (sys.version_info[0], sys.version_info[1])
if not rhplPath in sys.path:
    sys.path.append(rhplPath)

rhplPath="/usr/lib64/python%d.%d/site-packages/rhpl" % (sys.version_info[0], sys.version_info[1])
if not rhplPath in sys.path:
    sys.path.append(rhplPath)

import gtk.glade
import os
import string
import checklist
import servicemethods
from rhpl.translate import _, N_, cat

##
## I18N
## 
import gettext
gettext.bindtextdomain (domain, "/usr/share/locale")
gettext.textdomain (domain)
try:
    gettext.install(domain, "/usr/share/locale", 1)
except IOError:
    import __builtin__
    __builtin__.__dict__['_'] = unicode
_=gettext.gettext

quiting = 0
VERSION = "@VERSION@"

def verify_delete(arg):
    message=_("Are you sure you want to delete the %s?") % arg
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                            gtk.BUTTONS_YES_NO,
                            message)
    dlg.set_position(gtk.WIN_POS_MOUSE)
    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    return rc

def error_dialog (message, dialog_type=gtk.MESSAGE_WARNING):
    dialog = gtk.MessageDialog (None,
                                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                                dialog_type,
                                gtk.BUTTONS_OK,
                                message)
    dialog.set_position(gtk.WIN_POS_MOUSE)
    dialog.run ()
    dialog.destroy ()

def find_browser():
    try:
        path = '/usr/bin/mozilla'
        os.stat(path)
        return path
    except:
        try:
            path = '/usr/bin/galeon'
            os.stat(path)
            return path
        except:
            try:
                path = '/usr/bin/konqueror'
                os.stat(path)
                return path
            except:
                return None
        
class Gui:
    def destroy(self, args):
        if gtk.__dict__.has_key ("main_quit"):
            gtk.main_quit()
        else:
            gtk.mainquit()

    """This class handles everything gui for the system-config-services application"""
    def __init__(self):

        signal.signal (signal.SIGINT, signal.SIG_DFL)

        # make sure threading is disabled
        try:
            from gtk import _disable_gdk_threading
            _disable_gdk_threading()
        except ImportError:
            pass
        self.dirty=0
        self.previous=None
        self.ServiceMethods = servicemethods.ServiceMethods()

        gtk.glade.bindtextdomain(domain)

        if os.access("serviceconf.glade", os.R_OK) == 1:
            self.xml = gtk.glade.XML("serviceconf.glade", domain=domain)
        else:
            self.xml = gtk.glade.XML("/usr/share/system-config-services/serviceconf.glade", domain=domain)
        # map the event signals to specific methods
        self.xml.signal_autoconnect(
            {
              'on_winMain_delete_event' : self.quit,
              "on_mnuRescan_activate" : self.on_mnuRescan_activate,
              "on_mnuSave_activate" : self.on_mnuSave_clicked,
              "on_mnuRevert_activate" : self.on_mnuRevert_clicked,
              "on_mnuExit_activate" : self.quit,
              "on_add_service_activate" : self.on_add_service_clicked,
              "on_delete_service_activate" : self.on_delete_service_clicked,
              "on_mnuStart_activate" : self.on_btnStart_clicked,
              "on_mnuStop_activate" : self.on_btnStop_clicked,
              "on_mnuRestart_activate" : self.on_btnRestart_clicked,
              "on_pmnStart_activate" : self.on_btnStart_clicked,
              "on_pmnStop_activate" : self.on_btnStop_clicked,
              "on_pmnRestart_activate" : self.on_btnRestart_clicked,
              "on_mnuManual_activate" : self.on_mnuManual_activate,
              "on_edit_runlevel" : self.on_edit_runlevel,
              "on_optRL3_toggled" : self.on_optRL3_toggled,
              "on_optRL4_toggled" : self.on_optRL4_toggled,
              "on_optRL5_toggled" : self.on_optRL5_toggled ,
              "on_pmnStart_activate" : self.on_btnStart_clicked,
              "on_pmnStop_activate" : self.on_btnStop_clicked,
              "on_pmnRestart_activate" : self.on_btnRestart_clicked } )

        # main window
        self.winMain = self.xml.get_widget("winMain")
        self.winMain.connect("destroy", self.destroy)

        # menu items
        self.mnuRescan = self.xml.get_widget("mnuRescan")
        self.mnuSave = self.xml.get_widget("mnuSave")
        self.mnuRevert = self.xml.get_widget("mnuRevert")
        self.mnuExit = self.xml.get_widget("mnuExit")
        self.mnuAbout = self.xml.get_widget("mnuAbout")
        self.mnuStart = self.xml.get_widget("mnuStart")
        self.mnuStop = self.xml.get_widget("mnuStop")
        self.mnuRestart = self.xml.get_widget("mnuRestart")
        self.optRL3 = self.xml.get_widget("optRL3")
        self.optRL4 = self.xml.get_widget("optRL4")
        self.optRL5 = self.xml.get_widget("optRL5")
        
        self.optRL3= self.xml.get_widget("optRL3")
        self.optRL4= self.xml.get_widget("optRL4")
        self.optRL5= self.xml.get_widget("optRL5")

        #toolbars
        self.tbrSave = self.xml.get_widget("tbrSave")

        icon = gtk.Image()
        icon.set_from_stock("gtk-go-forward", gtk.ICON_SIZE_BUTTON)
        self.btnStart = self.tbrSave.append_item(_("Start"), _("Start"), None, icon, self.on_btnStart_clicked, None)

        icon = gtk.Image()
        icon.set_from_stock("gtk-stop", gtk.ICON_SIZE_BUTTON)
        self.btnStop = self.tbrSave.append_item(_("Stop"), _("Stop"), None, icon, self.on_btnStop_clicked, None)

        icon = gtk.Image()
        icon.set_from_stock("gtk-refresh", gtk.ICON_SIZE_BUTTON)
        self.btnRestart = self.tbrSave.append_item(_("Restart"), _("Restart"), None, icon, self.on_btnRestart_clicked, None)

        self.tbrSave.insert_space(3)

        icon = gtk.Image()
        icon.set_from_stock("gtk-save", gtk.ICON_SIZE_BUTTON)
        self.btnSave = self.tbrSave.append_item(_("_Save"), _("Save"), None, icon, self.on_mnuSave_clicked, None)
        self.btnSave.get_children()[0].get_children()[1].set_use_underline(gtk.TRUE)
        
        icon = gtk.Image()
        icon.set_from_stock("gtk-revert-to-saved", gtk.ICON_SIZE_BUTTON)
        self.btnRevert = self.tbrSave.append_item(_("_Revert"), _("Revert"), None, icon, self.on_mnuRevert_clicked, None)
        self.btnRevert.get_children()[0].get_children()[1].set_use_underline(gtk.TRUE)        

        # the textbox
        self.txtDesc = self.xml.get_widget("txtDesc")
	self.txtBuffer = gtk.TextBuffer(None)
	self.txtDesc.set_buffer(self.txtBuffer)

        # the statusbox
        self.txtStatus = self.xml.get_widget("StatusView")
	self.txtStatusBuffer = gtk.TextBuffer(None)
	self.txtStatus.set_buffer(self.txtStatusBuffer)

        self.lblRunlevel = self.xml.get_widget("lblRunlevel")
        self.lblEditing = self.xml.get_widget("lblEditing")
        
        self.editing_runlevel = self.ServiceMethods.get_runlevel()

        self.pmnStart = self.xml.get_widget("pmnStart")
        self.pmnStop = self.xml.get_widget("pmnStop")
        self.pmnRestart = self.xml.get_widget("pmnRestart")
        
        # the CheckCList which will display whether the service
        # is enabled, and the service names        
        
        self.clstServices = checklist.CheckList()
        self.xml.get_widget("swindow").add(self.clstServices)

        self.clstServices.show()
        self.ServiceMethods = servicemethods.ServiceMethods()

        # initialize this to the runlevel we are running in. It will
        # change when one of the optRL[3-6] are selected

        self.lblRunlevel.set_text (_("Currently Running in Runlevel: ") +         self.editing_runlevel)
        
        # This is a sentry
        self.already_init = 0
        self.populateList()
        self.toggled_service(0, 0)
        
        self.clstServices.get_selection ().connect ("changed", self.changed,None)

        self.clstServices.connect("button_press_event", self.local_button_press_cb)
        self.clstServices.checkboxrenderer.connect("toggled", self.toggled_service)
        self.clstServices.set_column_title(0,_("Start at Boot"))
        self.clstServices.set_column_title(1,_("Services"))
        #self.clstServices.set_column_justification(0,GTK.JUSTIFY_CENTER)
        #self.clstServices.set_column_justification(1,GTK.JUSTIFY_LEFT)
        #self.clstServices.set_column_auto_resize(0,1)
        #self.clstServices.column_titles_show()

        self.popup_menu = gtk.MenuItem()

        if self.editing_runlevel == "3" or self.editing_runlevel == "2" or self.editing_runlevel == "1":
            self.optRL3.set_active(1)

        elif self.editing_runlevel == "5" :
            self.optRL5.set_active(1)

        elif self.editing_runlevel == "4" :
            self.optRL4.set_active(1)

        self.save_revert_sensitive(0)
        
        self.clstServices.get_selection().select_path ((0,))
        self.changed(self.clstServices.get_selection(), None)
        self.current_selected_service = self.clstServices.get_text(0,1)

        self.winMain.show()



#-----------------------------------------------------------------------------
# Methods assiciated with populating the checklist
#-----------------------------------------------------------------------------
    def populateList(self):
        """Populates clstServices with the service names, whether it is configured, and service descriptions"""
        # sentinal so that we don't have selected rows while we are updating
        path=(0,)
        result = self.clstServices.get_selection().get_selected ()
        try:
            (model, iter) = result
            path = model.get_path (iter)
        except:
            pass

        self.am_updating = 1
        self.winMain.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        self.winMain.set_sensitive(0)
        self.clstServices.clear()

        if self.already_init == 0: 
            # this is passed to ServiceMethods.get_service_list as an
            # argument. We don't want to import gtk there, so we have
            # the actual function here
            def idle_func():
                while gtk.events_pending():
                    if gtk.__dict__.has_key ("main_iteration"):
                        gtk.main_iteration()
                    else:
                        gtk.mainiteration()
            self.allservices, self.dict_services = self.ServiceMethods.get_service_list(self.editing_runlevel, idle_func)
            self.dict_services_orig = self.ServiceMethods.dict_services_orig
            self.lblEditing.set_text(_("Editing Runlevel: ") + self.editing_runlevel)
            self.already_init = 1
        
        for servicename in self.allservices:
            self.clstServices.append_row((servicename, ""), int(self.dict_services[servicename][0][int(self.editing_runlevel)]))

        self.winMain.set_sensitive(1)
        self.winMain.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
        self.am_updating = 0
        self.clstServices.get_selection().select_path (path)
        
    def changed(self,selection, data):
        result = selection.get_selected ()
        if result != None:
            (model, iter) = result
            if iter != None:
                row = model.get_path(iter)[0]
                self.text_in_row = self.clstServices.get_text(int(row),1)
                self.set_text_buffer()
                self.set_text_status()
        
    def set_text_buffer(self):
        # set the text in txtDesc
        if self.ServiceMethods.dict_services.has_key(self.text_in_row):
            x = self.ServiceMethods.dict_services[self.text_in_row]
	    self.txtBuffer.set_text(string.strip(x[2]))
	# if an xinetd service is selected, disable these,
        # they'll do nothing
        if self.ServiceMethods.dict_services[self.text_in_row][1] == 1:
            self.action_widgets_sensitive(0)
        else:
            self.action_widgets_sensitive(1)
            
    def set_text_status(self):
        # set the text in StatusView
        message=""
        if self.ServiceMethods.dict_services[self.text_in_row][1] != 1:
            if self.ServiceMethods.dict_services.has_key(self.text_in_row):
                result = self.ServiceMethods.get_status(self.text_in_row)
                message=result[1]
                status=result[0]
            else:
                status=self.ServiceMethods.UNKNOWN
                message = _("Unknown")
        else:
            status=self.ServiceMethods.UNKNOWN
            result = self.ServiceMethods.get_status("xinetd")
            message=result[1]
        self.txtStatusBuffer.set_text(message.strip())

    def toggled_service(self, data, row):
        """Populates txtDesc with the service description of the service selected in clstServices"""
        self.text_in_row = self.clstServices.get_text(int(row),1)
        current_runlevel = int(self.editing_runlevel)
        self.current_selected = self.clstServices.get_text(int(row),1)

        #make sure we aren't updating
        if self.am_updating != 1:

            # enables and disables the save and revert buttons/menus
            # if something has been changed from it's orig setting
            for i in range(0,len(self.ServiceMethods.dict_services_orig)-1):
                self.checking_service = self.clstServices.get_text(i,1)
                service_enabled = int("%d" % self.clstServices.get_active(i))
                

                if service_enabled == self.ServiceMethods.dict_services_orig[self.checking_service][0][current_runlevel]:
                    self.save_revert_sensitive(0)
                    
                elif service_enabled != self.ServiceMethods.dict_services_orig[self.checking_service][0][current_runlevel]:
                    self.save_revert_sensitive(1)
                    break


        return self.text_in_row


            
#----------------------------------------------------------------------------
# Methods pertaining to the "File" menu items
# The "Save Changes", "Revert to Last Save" and "Quit" menu items are handled
# elsewhere by on_mnuSave_clicked(), on_mnuRevert_clicked(), and
# "Exit" just calls gtk.main_quit()
#----------------------------------------------------------------------------    
    def on_mnuRescan_activate(self,args):
        """clears clstServices, and reruns populateList()"""

        # set the cursor while we are busy
        self.already_init = 0
        self.populateList()


#----------------------------------------------------------------------------
# Methods pertaining to the "Edit Runlevel" menu items 
#----------------------------------------------------------------------------
    def on_optRL3_toggled(self, button):
        """calls  populateList() to repopulate the checklist for runlevel 3"""
        if self.previous==button:
            return
        if button.get_active() != gtk.TRUE:
            self.previous=button
            return
        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            self.previous.set_active(1)
            return gtk.TRUE
        self.editing_runlevel = "3"
        self.lblEditing.set_text(_("Editing Runlevel: ") + self.editing_runlevel)
        self.populateList()



    def on_optRL4_toggled(self, button):
        """calls populateList() to repopulate the checklist for runlevel 4"""
        if self.previous==button:
            return
        if button.get_active() != gtk.TRUE:
            self.previous=button
            return

        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            self.previous.set_active(1)
            return gtk.TRUE
        self.editing_runlevel = "4"
        self.lblEditing.set_text(_("Editing Runlevel: ") + self.editing_runlevel)
        self.populateList()

    def on_edit_runlevel(self, button):
        self.optRL3.set_sensitive(not self.dirty)
        self.optRL4.set_sensitive(not self.dirty)
        self.optRL5.set_sensitive(not self.dirty)
        
    def on_optRL5_toggled(self, button):
        """calls populateList() to repopulate the checklist for runlevel 5"""
        if self.previous==button:
            return
        if button.get_active() != gtk.TRUE:
            self.previous=button
            return
        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            self.previous.set_active(1)
            return gtk.TRUE
        self.editing_runlevel = "5"
        self.lblEditing.set_text(_("Editing Runlevel: ") + self.editing_runlevel)
        self.populateList()

    def check_dirty(self):
        rc=gtk.RESPONSE_YES
        """Check to see if the user has any unsaved changes."""
        if self.dirty:
            dlg = self.xml.get_widget ("saveDialog")
            rc = dlg.run()
            dlg.hide()
            
            if rc==gtk.RESPONSE_YES:
                try:
                    self.on_mnuSave_clicked(None)
                except IOError:
                    pass
            if rc!=gtk.RESPONSE_CANCEL:
                self.dirty=0
        return rc
    


#----------------------------------------------------------------------------
# Methods pertaining to the "Help" menu items, there will be more here
# once I have "real" help :)
#----------------------------------------------------------------------------
    def on_mnuAbout_activate(self,Dummy):
        """Just a silly about dialog"""
        dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                 _("System Services Configuration Tool VERSION\n Copyright (c) 2002-2004 "
                                   "Red Hat, Inc.\n Tim Powers <timp@redhat>\n "
                                   "Bill Nottingham <notting@redhat>\n Dan Walsh <dwalsh@redhat.com>\n "
                                   "Brent Fox <bfox@redhat.com>\n "))
        dlg.set_title(_("About"))
        dlg.set_default_size(100, 100)
        dlg.set_position (gtk.WIN_POS_CENTER)
        dlg.set_border_width(2)
        dlg.set_modal(gtk.TRUE)
        dlg.set_transient_for(self.winMain)

        iconPixbuf = None
        try:
            iconPixbuf = gtk.gdk.pixbuf_new_from_file("/usr/share/system-config-services/system-config-services.png")
        except:
            pass
        
        if iconPixbuf:
            dlg.set_icon(iconPixbuf)
        rc = dlg.run()
        dlg.destroy()

#----------------------------------------------------------------------------
# Methods pertaining to the "Help" menu items, there will be more here
# once I have "real" help :)
#----------------------------------------------------------------------------
    def on_mnuManual_activate(self,args):
        help_page = "file:///usr/share/doc/system-config-services-" + VERSION + "/html/index.html"

        path = "/usr/bin/htmlview"
         
        if path == None:
            dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("Help is not available.")))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.run()
            dlg.destroy()
            return
                 
        pid = os.fork()
        if not pid:
            os.execv(path, [path, help_page])

    def on_selectCursor(self,args):
        """calls get_service_action_results to start the selected initscript"""
        print "on_selectCursor"

#----------------------------------------------------------------------------
# Methods pertaining to the toolbar items
# The menu and popup menu items for "Start", "Stop", and "Restart" are
# handled by on_btnStart_clicked(), on_btnStop_clicked(), and 
# on_btnRestart_clicked()
#----------------------------------------------------------------------------
    def on_mnuSave_clicked(self, args):
        """Commits the changes made for each service"""
        for i in range(0,len(self.ServiceMethods.dict_services)):
            servicename = self.clstServices.get_text(i,1)
            service_enabled = "%d" % self.clstServices.get_active(i)
            self.ServiceMethods.save_changes(servicename, service_enabled, self.editing_runlevel)

        self.save_revert_sensitive(0)

    def quit(self,arg1=None,arg2=None):
        global quiting
        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            return  gtk.TRUE
        quiting=1
        if gtk.__dict__.has_key ("main_quit"):
            gtk.main_quit()
        else:
            gtk.mainquit()
        
    def on_mnuRevert_clicked(self, args):
        """calls populateList() to repopulate the checklist"""
        self.populateList()
        self.save_revert_sensitive(0)


    def get_service_action_results(self, servicename, action_type):
        """calls ServiceMethods.service_action_results and displays the results in a dialog box"""

        self.winMain.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        results = self.ServiceMethods.service_action_results(servicename, action_type, self.editing_runlevel)

        if int(results[0]) != 0:
            dlg = gtk.MessageDialog(self.winMain, 0, gtk.MESSAGE_ERROR,
	    	gtk.BUTTONS_OK, results[1])
        else:
            dlg = gtk.MessageDialog(self.winMain, 0, gtk.MESSAGE_INFO,
	    	gtk.BUTTONS_OK, results[1])
        dlg.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
	dlg.show_all()
	rc = dlg.run()
	dlg.destroy()
        self.set_text_status()
        self.winMain.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))

    def on_add_service_clicked(self,args):
        dlg = self.xml.get_widget ("serviceNameDialog")
        rc = dlg.run()
        dlg.hide()
            
        if rc==gtk.RESPONSE_OK:
            service=self.xml.get_widget ("serviceNameEntry").get_text()
            response=self.ServiceMethods.chkconfig_add_service(service)
            if response[0]!=0:
                error_dialog(response[1])
            else:
                self.on_mnuRescan_activate(None)

    def on_delete_service_clicked(self,args):
        if verify_delete(self.current_selected) == gtk.RESPONSE_YES:
            response=self.ServiceMethods.chkconfig_delete_service(self.current_selected)
            if response[0]!=0:
                error_dialog(response[1])
            else:
                self.on_mnuRescan_activate(None)
            
    def on_btnStart_clicked(self, *args):
        """calls get_service_action_results to start the selected initscript"""
        self.get_service_action_results(self.text_in_row, "start")

    def on_btnStop_clicked(self, *args):
        """calls get_service_action_results to stop the selected initscript"""
        self.get_service_action_results(self.text_in_row, "stop")

    def on_btnRestart_clicked(self,args):
        """calls get_service_action_results to restart the selected initscript"""
        self.get_service_action_results(self.text_in_row, "restart")



#----------------------------------------------------------------------------
# Methods for everything else
#----------------------------------------------------------------------------
    def local_button_press_cb (self, clist, event):
        """checks to see if the third mouse button was clicked. If it was, then bring up the popup menu"""
        row=clist.get_path_at_pos (int(event.x),int(event.y))[0][0]
        self.text_in_row = self.clstServices.get_text(int(row),1)
        self.current_selected = self.clstServices.get_text(int(row),1)
        self.set_text_buffer()
        self.set_text_status()
        if (event.button == 3):
            self.popupMenu = self.xml.get_widget ("popup_menu")

            # get rid of the tearoff from the popup menu
            self.pmnBlank = self.xml.get_widget ("pmnBlank")
            # set the label text to be the current selected servicename for pmnBlank
            self.pmnBlank.get_children ()[0].set_text (self.current_selected)
            self.popupMenu.popup(None, None, None, event.button, event.time)


    def save_revert_sensitive(self, sensitive):
        """sets the save and revert buttons and menus to be sensitive or not, sensitive is a 1 or 0"""
        self.mnuSave.set_sensitive(sensitive)
        self.mnuRevert.set_sensitive(sensitive)
        self.btnSave.set_sensitive(sensitive)
        self.btnRevert.set_sensitive(sensitive)
        self.dirty=sensitive

    def action_widgets_sensitive(self, sensitive):
        """sets the start/stop/restart buttons and menuitems to be sensitive or not"""
        self.btnStart.set_sensitive(sensitive)
        self.btnRestart.set_sensitive(sensitive)
        self.btnStop.set_sensitive(sensitive)
        self.mnuStart.set_sensitive(sensitive)
        self.mnuStop.set_sensitive(sensitive)
        self.mnuRestart.set_sensitive(sensitive)
        self.pmnStart.set_sensitive(sensitive)
        self.pmnStop.set_sensitive(sensitive)
        self.pmnRestart.set_sensitive(sensitive)
                                    
        
def main():
    if os.geteuid() == 0:
        try:
            Gui()
            if gtk.__dict__.has_key ("main"):
                gtk.main ()
            else:
                gtk.mainloop ()
        except:
            # if you quit during initialization exceptions can be raised
            if not quiting:
                raise
    else:
        print _("You must run system-config-services as root.")
        sys.exit(-1)


    
if __name__ == "__main__":
    main() 
