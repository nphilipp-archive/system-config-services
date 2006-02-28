#!/usr/bin/python
# -*- coding: utf-8 -*-
""" system-config-services: This module contains the Gui class which contains the methods pertaining to the gui only """
# serviceconf.py
# Copyright © 2002-2006 Red Hat, Inc.
# Authors: Tim Powers <timp@redhat.com>
#          Bill Nottingham <notting@redhat.com>
#          Dan Walsh <dwalsh@redhat.com>
#          Nils Philippsen <nphilipp@redhat.com>
#          Florian Festi <ffesti@redhat.com>
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
from servicemethods import *
from rhpl.translate import _, N_, cat

##
## I18N
## 
import gettext
gettext.bindtextdomain(domain, "/usr/share/locale")
gettext.textdomain(domain)
try:
    gettext.install(domain, "/usr/share/locale", 1)
except IOError:
    import __builtin__
    __builtin__.__dict__['_'] = unicode
_=gettext.gettext

quitting = 0
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

def error_dialog(message, dialog_type=gtk.MESSAGE_WARNING):
    dialog = gtk.MessageDialog(None,
                                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                                dialog_type,
                                gtk.BUTTONS_OK,
                                message)
    dialog.set_position(gtk.WIN_POS_MOUSE)
    dialog.run()
    dialog.destroy()

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

def idle_func():
    while gtk.events_pending():
        if gtk.__dict__.has_key("main_iteration"):
            gtk.main_iteration()
        else:
            gtk.mainiteration()


class RunlevelCheckList(checklist.CheckList):
    def __init__(self):
        checklist.CheckList.__init__(self, 7)
        self.set_column_visible(0, True)

    def set_column_visible(self, column, visible):
        checklist.CheckList.set_column_visible(self, column, visible)

        not_visible_before = True
        for i in range(0, 7):
            acol = self.get_column(i)
            if acol:
               if not_visible_before:
                   acol.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
                   acol.set_alignment(1.0)
                   for cr in acol.get_cell_renderers():
                       cr.set_property('xalign', 0.7)
                   self.set_column_title(i, _('Runlevel %d') % i)
               else:
                   acol.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                   acol.set_alignment(0.5)
                   for cr in acol.get_cell_renderers():
                       cr.set_property('xalign', 0.5)
                   self.set_column_title(i, '%d' % i)

               if acol.get_visible():
                   not_visible_before = False

class Gui:
    def destroy(self, args):
        if gtk.__dict__.has_key("main_quit"):
            gtk.main_quit()
        else:
            gtk.mainquit()

    def uicallback(self):
        while gtk.events_pending():
            if gtk.__dict__.has_key("main_iteration"):
                gtk.main_iteration()
            else:
                gtk.mainiteration() 

    """This class handles everything gui for the system-config-services application"""
    def __init__(self):

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # make sure threading is disabled
        try:
            from gtk import _disable_gdk_threading
            _disable_gdk_threading()
        except ImportError:
            pass
        self.dirty=0
        self.previous=None
        self.services = Services(self.uicallback)

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
              "on_optRLA_toggled" : self.on_optRLA_toggled ,
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
        self.optRLA = self.xml.get_widget("optRLA")

        #toolbars
        #self.tbrSave = self.xml.get_widget("tbrSave")

        self.btnStart = self.xml.get_widget('btnStart')
        self.xml.signal_connect('on_btnStart_clicked', self.on_btnStart_clicked)

        self.btnStop = self.xml.get_widget('btnStop')
        self.xml.signal_connect('on_btnStop_clicked', self.on_btnStop_clicked)

        self.btnRestart = self.xml.get_widget('btnRestart')
        self.xml.signal_connect('on_btnRestart_clicked', self.on_btnRestart_clicked)

        self.btnSave = self.xml.get_widget('btnSave')
        self.xml.signal_connect('on_btnSave_clicked', self.on_mnuSave_clicked)
        self.btnSave.get_children()[0].get_children()[0].get_children()[1].set_use_underline(True)
        
        self.btnRevert = self.xml.get_widget('btnRevert')
        self.xml.signal_connect('on_btnRevert_clicked', self.on_mnuRevert_clicked)
        self.btnRevert.get_children()[0].get_children()[0].get_children()[1].set_use_underline(True)        

        #### background services ####

        # the textbox
        self.bgTxtDesc = self.xml.get_widget("bgTxtDesc")
        self.bgTxtDescBuffer = gtk.TextBuffer(None)
        self.bgTxtDesc.set_buffer(self.bgTxtDescBuffer)

        # the statusbox
        self.bgTxtStatus = self.xml.get_widget("bgTxtStatus")
        self.bgTxtStatusBuffer = gtk.TextBuffer(None)
        self.bgTxtStatus.set_buffer(self.bgTxtStatusBuffer)

        self.lblRunlevel = self.xml.get_widget("lblRunlevel")
        self.lblEditing = self.xml.get_widget("lblEditing")
        
        self.editing_runlevel = self.services.get_runlevel()

        self.pmnStart = self.xml.get_widget("pmnStart")
        self.pmnStop = self.xml.get_widget("pmnStop")
        self.pmnRestart = self.xml.get_widget("pmnRestart")
        
        # the CheckList which will display whether the service
        # is enabled, and the service names        
        self.bgListServices = RunlevelCheckList()
        self.xml.get_widget("bgScrolledWindow").add(self.bgListServices)

        self.bgListServices.show()

        # initialize this to the runlevel we are running in. It will
        # change when one of the optRL[3-6] are selected
        self.lblRunlevel.set_text(_("Currently Running in Runlevel: ") + str (self.editing_runlevel))
        
        self.bgListServices.get_selection().connect("changed", self.changed, self.bgListServices)

        self.bgListServices.connect("button_press_event", self.local_button_press_cb)
        self.popup_menu = gtk.MenuItem()

        self.optRL3.set_active(0)
        self.optRL4.set_active(0)
        self.optRL5.set_active(0)
        self.optRLA.set_active(0)
        
        self.save_revert_sensitive(0)
        
        #### xinetd/"on demand" services ####

        # the textbox
        self.odTxtDesc = self.xml.get_widget("odTxtDesc")
        self.odTxtDescBuffer = gtk.TextBuffer(None)
        self.odTxtDesc.set_buffer(self.odTxtDescBuffer)

        # the statusbox
        self.odTxtStatus = self.xml.get_widget("odTxtStatus")
        self.odTxtStatusBuffer = gtk.TextBuffer(None)
        self.odTxtStatus.set_buffer(self.odTxtStatusBuffer)

        # the CheckList which will display whether the service
        # is enabled, and the service names        
        self.odListServices = checklist.CheckList()
        self.xml.get_widget("odScrolledWindow").add(self.odListServices)

        self.odListServices.get_selection().connect("changed", self.changed, self.odListServices)
        self.odListServices.show()

        # This is a sentry
        self.already_init = 0
        self.populateList()
        # XXX self.toggled_service(0, 0, self.bgListServices)
        #self.toggled_service(0, 0, self.odListServices)
        
        self.bgListServices.get_selection().select_path((0,))
        self.changed(self.bgListServices.get_selection(), self.bgListServices)

        #### select runlevel ####
        map(lambda x: self.bgListServices.set_column_visible(x, 0), range(0, 7))
        if self.editing_runlevel == "3" or self.editing_runlevel == "2" or self.editing_runlevel == "1":
            self.bgListServices.set_column_visible(3, 1)
            self.optRL3.set_active(1)

        elif self.editing_runlevel == "4" :
            self.bgListServices.set_column_visible(4, 1)
            self.optRL4.set_active(1)

        else:
            self.bgListServices.set_column_visible(5, 1)
            self.optRL5.set_active(1)

        for s in (self.bgListServices, self.odListServices):
            for i in range(0, s.num_checkboxes):
                s.checkboxrenderer[i].connect("toggled", self.toggled_service,
                                              i, s)

        self.winMain.show()

#-----------------------------------------------------------------------------
# Methods assiciated with populating the checklist
#-----------------------------------------------------------------------------
    def populateList(self):
        """Populates {bg,od}ListServices with the service names, whether it is configured, and service descriptions"""
        # sentinel so that we don't have selected rows while we are updating
        bgpath = (0,)
        odpath = (0,)

        result = self.bgListServices.get_selection().get_selected()
        try:
            (model, iter) = result
            bgpath = model.get_path(iter)
        except:
            pass

        result = self.odListServices.get_selection().get_selected()
        try:
            (model, iter) = result
            odpath = model.get_path(iter)
        except:
            pass

        self.am_updating = 1
        self.winMain.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        self.winMain.set_sensitive(0)
        self.bgListServices.clear()
        self.odListServices.clear()

        if self.already_init == 0: 
            self.services.get_service_lists()
            
            self.lblEditing.set_text(_("Editing Runlevel: ") + str (self.editing_runlevel))
            self.already_init = 1
        
        for service in self.services:
            if service.hide: continue
            self.bgListServices.append_row(service.name, service.get_runlevels())
        for service in self.services.xinetd_services():
            if service.hide: continue
            self.odListServices.append_row(service.name, service.get_runlevels())

        self.winMain.set_sensitive(1)
        self.winMain.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
        self.am_updating = 0
        self.bgListServices.get_selection().select_path(bgpath)
        self.odListServices.get_selection().select_path(odpath)
        
    def changed(self, selection, list):
        result = selection.get_selected()
        if result != None:
            (model, iter) = result
            if iter != None:
                row = model.get_path(iter)[0]
                self.text_in_row = list.get_text(int(row), list.num_checkboxes)
                if list == self.bgListServices:
                    desc = self.bgTxtDescBuffer
                    status = self.bgTxtStatusBuffer
                elif list == self.odListServices:
                    desc = self.odTxtDescBuffer
                    status = self.odTxtStatusBuffer
                self.set_desc_buffer(desc)
                self.set_status_buffer(status)
        
    def set_desc_buffer(self, buf):
        # set the text in {bg,od}TxtDesc
        service = self.services[self.text_in_row]
        buf.set_text(service.description)
        # if an xinetd service is selected, disable these,
        # they'll do nothing
        if service.is_xinetd_service():
            self.action_widgets_sensitive(0)
        else:
            self.action_widgets_sensitive(1)
            
    def set_status_buffer(self, buf):
        # set the text in {bg,od}TxtStatus
        print self.text_in_row
        if not self.services.has_key(self.text_in_row):
            status = UNKNOWN
            message = _("Unknown")
        else:                   
            service = self.services[self.text_in_row]
            message=""
            if not service.is_xinetd_service():
                # background service/daemon
                status = service.status
                message = service.status_message
            else:
                # on demand/xinetd service
                status = UNKNOWN
                message = self.services["xinetd"].status_message
        print message
        buf.set_text(message)

    def toggled_service(self, toggle, row, column, list):
        """Updates self.services if buttons are toggled
        in {bg,od}ListServices"""
        #make sure we aren't updating
        if self.am_updating != 1:
            row = int(row)
            self.text_in_row = list.get_text(row, list.num_checkboxes)

            service = self.services[self.text_in_row]
            enabled = not toggle.get_active() # we are before the change?

            service.set_in_runlevels(enabled, column)

            changed = self.services.is_changed()
            self.save_revert_sensitive(changed)
            
        return self.text_in_row

#----------------------------------------------------------------------------
# Methods pertaining to the "File" menu items
# The "Save Changes", "Revert to Last Save" and "Quit" menu items are handled
# elsewhere by on_mnuSave_clicked(), on_mnuRevert_clicked(), and
# "Exit" just calls gtk.main_quit()
#----------------------------------------------------------------------------    
    def on_mnuRescan_activate(self,args):
        """clears bgListServices, and reruns populateList ()"""

        # set the cursor while we are busy
        self.already_init = 0
        self.populateList()


#----------------------------------------------------------------------------
# Methods pertaining to the "Edit Runlevel" menu items 
#----------------------------------------------------------------------------
    def set_editing_runlevels(self, button, title, runlevels):
        if self.previous==button:
            return
        if button.get_active() != True:
            self.previous=button
            return
        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            self.previous.set_active(1)
            return True

        self.editing_runlevel = title
        self.lblEditing.set_text(_("Editing Runlevel: ") + title)

        if isinstance(runlevels, int):
            runlevels = [runlevels]
            self.bgListServices.set_headers_visible(0)        
        else:
            self.bgListServices.set_headers_visible(1)
        rl_map = map(lambda x: 0, range(0,7))
        for rl in runlevels:
            rl_map[rl] = 1
        for i in range(0,7):
            if self.bgListServices.get_column_visible(i) != rl_map[i]:
                self.bgListServices.set_column_visible(i, rl_map[i])
        self.populateList()

    def on_optRL3_toggled(self, button):
        """calls  populateList() to repopulate the checklist for runlevel 3"""
        return self.set_editing_runlevels(button, "3", 3)

    def on_optRL4_toggled(self, button):
        """calls populateList() to repopulate the checklist for runlevel 4"""
        return self.set_editing_runlevels(button, "4", 4)

    def on_optRL5_toggled(self, button):
        """calls populateList() to repopulate the checklist for runlevel 5"""
        return self.set_editing_runlevels(button, "5", 5)

    def on_optRLA_toggled(self, button):
        """calls populateList() to repopulate the checklist for all runlevels"""
        return self.set_editing_runlevels(button, _("All"), [3, 4, 5])

    def on_edit_runlevel(self, button):
        self.optRL3.set_sensitive(not self.dirty)
        self.optRL4.set_sensitive(not self.dirty)
        self.optRL5.set_sensitive(not self.dirty)
        self.optRLA.set_sensitive(not self.dirty)

    def check_dirty(self):
        rc=gtk.RESPONSE_YES
        """Check to see if the user has any unsaved changes."""
        if self.dirty:
            dlg = self.xml.get_widget("saveDialog")
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
        dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                 _("System Services Configuration Tool VERSION\n Copyright © 2002-2006 "
                                   "Red Hat, Inc.\n Tim Powers <timp@redhat.com>\n "
                                   "Bill Nottingham <notting@redhat.com>\n Dan Walsh <dwalsh@redhat.com>\n "
                                   "Brent Fox <bfox@redhat.com>\n Nils Philippsen <nphilipp@redhat.com>\n "))
        dlg.set_title(_("About"))
        dlg.set_default_size(100, 100)
        dlg.set_position(gtk.WIN_POS_CENTER)
        dlg.set_border_width(2)
        dlg.set_modal(True)
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
        self.services.save_changes()
        self.save_revert_sensitive(0)

    def quit(self,arg1=None,arg2=None):
        global quitting
        if self.check_dirty() == gtk.RESPONSE_CANCEL:
            return  True
        quitting=1
        if gtk.__dict__.has_key("main_quit"):
            gtk.main_quit()
        else:
            gtk.mainquit()
        
    def on_mnuRevert_clicked(self, args):
        """calls populateList() to repopulate the checklist"""
        self.populateList()
        self.save_revert_sensitive(0)


    def get_service_action_results(self, servicename, action_type):
        """calls services[servicename].action and
        displays the results in a dialog box"""

        self.winMain.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        results = self.services[servicename].action(action_type)

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
        self.set_desc_buffer(self.bgTxtDescBuffer)
        self.set_status_buffer(self.bgTxtStatusBuffer)
        self.winMain.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))

    def on_add_service_clicked(self,args):
        dlg = self.xml.get_widget("serviceNameDialog")
        rc = dlg.run()
        dlg.hide()
            
        if rc==gtk.RESPONSE_OK:
            service=self.xml.get_widget("serviceNameEntry").get_text()
            response=self.services.add_service(service)
            if response[0]!=0:
                error_dialog(response[1])
            else:
                self.on_mnuRescan_activate(None)

    def on_delete_service_clicked(self,args):
        if verify_delete(self.current_selected) == gtk.RESPONSE_YES:
            response=self.services.delete_service(self.current_selected)
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
    def local_button_press_cb(self, clist, event):
        """checks to see if the third mouse button was clicked. If it was, then bring up the popup menu"""
        row=clist.get_path_at_pos(int(event.x),int(event.y))[0][0]
        self.text_in_row = self.bgListServices.get_text(int(row),7)
        self.current_selected = self.bgListServices.get_text(int(row),7)
        self.set_desc_buffer(self.bgTxtDescBuffer)
        self.set_status_buffer(self.bgTxtStatusBuffer)
        if (event.button == 3):
            self.popupMenu = self.xml.get_widget("popup_menu")

            # get rid of the tearoff from the popup menu
            self.pmnBlank = self.xml.get_widget("pmnBlank")
            # set the label text to be the current selected servicename for pmnBlank
            self.pmnBlank.get_children()[0].set_text(self.current_selected)
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
        #try:
            Gui()
            if gtk.__dict__.has_key("main"):
                gtk.main()
            else:
                gtk.mainloop()
        #except:
        #    # if you quit during initialization exceptions can be raised
        #    if not quitting:
        #        raise
    else:
        print _("You must run system-config-services as root.")
        sys.exit(-1)


    
if __name__ == "__main__":
    main() 
