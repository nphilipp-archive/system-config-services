#!/bin/env python

import gtk.glade, sys, os
from rhpl.translate import _
from servicemethods import *

def newServiceControl(glade, functionname, widget_name,
                      string1, string2, int1, int2):
    """Factory function to be used with libglade"""
    if functionname == "ServiceControl": 
        return ServiceControl(service_name=string1).widget
    elif functionname == "ServiceStatus":
        return ServiceStatus()

def idle_func():
    while gtk.events_pending():
        if gtk.__dict__.has_key("main_iteration"):
            gtk.main_iteration()
        else:
            gtk.mainiteration()


class GladeWidget:

    def getWidgets(self, *names):
        for name in names:
            widget = self.xml.get_widget(name)
            if widget is None:
                raise ValueError, "Widget '%s' not found" % name
            setattr(self, name, widget)

class ServiceStatusBase:

    def __init__(self, service_name):
        # Get icons
        self.services = Services(idle_func)
        self.services.get_service_lists(service_name)
        self.service = self.services[service_name]
        self.service.subscribe(self.update)
        if self.service.is_xinetd_service():
            self.xinetd = self.service = self.services["xinetd"]

        self.tooltips = gtk.Tooltips()

    stockname = {
        'red' : 'gtk-dialog-error',
        'yellow' : 'gtk-dialog-warning',
        'green': 'gtk-execute',
        'off' : 'gtk-stop',
        }

    def _setIcon(self, state):        
        self.imgStatus.set_from_stock(self.stockname[state], 1)

    def _setState(self):
        status = self.service.status
        name = self.service.name

        if not self.service.exists():
            self._setIcon('red')
            self.lblStatus.set_text(_("Service %s not found!") % name)
            return

        if status == RUNNING:
            if self.service.is_dirty():
                self._setIcon('yellow')
                self.lblStatus.set_text(_("Service %s is running with old config") % name) 
            else:
                self._setIcon('green')
                self.lblStatus.set_text(_("Service %s is running") % name) 
        elif status == ERROR:
            self._setIcon('red')
            self.lblStatus.set_text(_("Service %s resports an error") % name) 
        else:
            self._setIcon('off')
            self.lblStatus.set_text(_("Service %s is stopped") % name) 
        self.tooltips.set_tip(self.lblStatus.parent, self.service.status_message)
        self.tooltips.set_tip(self.imgStatus.parent, self.service.status_message)

    def on_servicestatus_show(self, widget):
        self._setState()

    def update(self, service, data=None):
        self._setState()

class ServiceStatus(ServiceStatusBase, GladeWidget):
    """Status bar widget"""
    def __init__(self, service_name):

        ServiceStatusBase.__init__(self, service_name)
        
        self.xml = gtk.glade.XML(
            os.path.join(gladepath, "servicetab.glade"), root="servicestatus")
        self.getWidgets('servicestatus', 'lblStatus', 'imgStatus')
        self.widget = self.servicestatus
        self.xml.signal_autoconnect(self)
        self._setState()

class ServiceControlBase:

    def __init__(self, service_name, configure=True):
        self.uicallback = idle_func
        self.services = Services(idle_func)
        self.services.get_service_lists(service_name)
        self.service = self.services[service_name]
        self.tooltips = gtk.Tooltips()

        if self.service.is_xinetd_service():
            if hasattr(self, 'ReStart'):
                self.ReStart.hide()
                self.ReStart.set_no_show_all(True)
            else:
                self.Start.hide()
                self.Start.set_no_show_all(True)
                self.Restart.hide()
                self.Restart.set_no_show_all(True)
            self.Stop.hide()
            self.Stop.set_no_show_all(True)
            self.separator1.hide()
            self.separator1.set_no_show_all(True)

        if not configure:
            self.separator2.hide()
            self.separator2.set_no_show_all(True)
            self.Configure.hide()
            self.Configure.set_no_show_all(True)

    # ----------        

    def set_dirty(self, on):
        self._dirty = on

    def _setTooltip(self, widget, tip):
        if hasattr(widget, 'set_tooltip'):
            widget.set_tooltip(self.tooltips, tip)
        else:
            self.tooltips.set_tip(widget, tip)

    def _setStart(self, on):
        if hasattr(self, 'ReStart'):
            if on:
                icon = gtk.image_new_from_icon_name("reload", 1)
                self.ReStart.set_image(icon)
                icon.show()
                self.ReStart.set_label("Restart")
            else:
                icon = gtk.image_new_from_icon_name("forward", 1)
                self.ReStart.set_image(icon)
                self.ReStart.set_label("Start")
                icon.show()
        else:
             self.Start.set_sensitive(not on)
             self.Restart.set_sensitive(on)
        self.Stop.set_sensitive(on)

    def _setExists(self):
        on = self.service.exists()
        if hasattr(self, 'ReStart'):
            self.ReStart.set_sensitive(on)
        else:
            self.Start.set_sensitive(on)
            self.Restart.set_sensitive(on)
        self.Stop.set_sensitive(on)
        self.Enable.set_sensitive(on)
        self.Disable.set_sensitive(on)

    def _setState(self):
        self._setExists()
        if self.service.exists():
            self._setStart(self.service.status==RUNNING)
            self._setRunlevelStatus()
            
    def _setRunlevelStatus(self):
        buttons = isinstance(self.Enable, (gtk.ToolButton, gtk.Button))
        if self.service.is_default():
            on = self.service.is_default_on()
            self.Enable.set_sensitive(not on)
            self.Disable.set_sensitive(on)
            if on:                
                self._setTooltip(self.Enable, None)
                if self.service.is_xinetd_service():
                    self._setTooltip(self.Disable, None)
                else:
                    self._setTooltip(
                        self.Disable, _("Currently enabled in runlevels %s") %
                        self.service.get_active_runlevels_text())
            else:
                self._setTooltip(self.Disable, None)
                if self.service.is_xinetd_service():
                    self._setTooltip(self.Enable, None)
                else:
                    self._setTooltip(
                        self.Enable, _("Enable %(name)s in runlevels %(levels)s") %
                        { 'name' : self.service.name, 
                          'levels' : self.service.get_default_runlevels_text() } )
        else:
            self.Enable.set_sensitive(True)
            self.Disable.set_sensitive(True)
            self._setTooltip(
                self.Disable, _("Currently enabled in runlevels %s") % 
                self.service.get_active_runlevels_text())
            self._setTooltip(
                self.Enable, _("Enable %(name)s in runlevels %(levels)s") %
                { 'name' : self.service.name, 
                  'levels' : self.service.get_default_runlevels_text()} )

    def on_servicetab_show(self, widget):
        self._setState()

    def on_Start_clicked(self, button):
        self.service.action('start')
        self._setState()

    def on_Restart_clicked(self, button):
        if self.service.status == RUNNING:
            self.service.action('restart')
        else:
            self.service.action('start')
        self._setState()
        
    def on_Stop_clicked(self, button):
        self.service.action('stop')
        self._setState()

    def on_Runlevels_clicked(self, button):
        err, message = getstatusoutput("/usr/bin/system-config-services",
                                       self.uicallback)
        self._setState()

    def on_Enable_clicked(self, button):
        self.service.set(True)
        self.service.save_changes()
        self._setState()

    def on_Disable_clicked(self, button):
        self.service.set(False)
        self.service.save_changes()        
        self._setState()

    def on_Configure_clicked(self, button):
        # XXX
        pass

    def _toggleRunlevel(self, button, nr):
        if button.get_icon_widget().get_icon_name() == "ok":
            pass
        else:
            pass

    def setDirty(self):
        if self.serviceState== "on":
            self._setState("dirty")
        
    def openServicesTool(self, button):
        pid = os.fork()
        if not pid:
            path = "/usr/bin/system-config-services"
            os.execv(path, [path])

class ServiceControlWidget(ServiceControlBase, GladeWidget):
    
    widget_name = None
    
    def __init__(self, service_name, configure=True):
        self.xml = gtk.glade.XML(os.path.join(gladepath, "servicetab.glade"), root=self.widget_name)
        self.widget = self.xml.get_widget(self.widget_name)
        self.xml.signal_autoconnect(self)
        self.getWidgets('Start', 'Stop', 'Restart', 'separator1', 'Enable', 'Disable', 'separator2', 'Configure')

        ServiceControlBase.__init__(self, service_name, configure)

        self.service.subscribe(self.update)
        self._setState()
        
    def update(self, service, userdata=None):
        self._setState()

class ServiceControlButtons(ServiceControlWidget):
    widget_name = "ServiceControlButtons"
class ServiceControlToolbar(ServiceControlWidget):
    widget_name = "ServiceControlToolbar"
class ServiceMenu(ServiceControlWidget):
    widget_name = "ServiceMenu"

class ServiceTab(ServiceControlBase, GladeWidget):
    """Widget for controlling a service"""
    def __init__(self, service_name):
        ServiceControlBase.__init__(self, service_name)
        self.xml = gtk.glade.XML(
            os.path.join(gladepath, "servicetab.glade"), root="servicetab")

        # set as attributes
        self.getWidgets('Enable', 'Disable', 'Runlevels',
                        'lblRunlevel', 'lblEditingRunlevels',
                        'ReStart', 'Stop',
                        'servicetab')
        self.widget = self.servicetab
        self.xml.signal_autoconnect(self)
        self._setState()

        runlevel = self.services.get_runlevel()
        self.lblRunlevel.set_text(self.lblRunlevel.get_text() % runlevel)
        if self.service.defaultrunlevels:
            self.lblEditingRunlevels.set_text(
                "Changing runlevel %s (default runlevel)" %
                ",".join(self.service.defaultrunlevels))
        else:
            self.service.defaultrunlevels.append(runlevel)
            self.lblEditingRunlevels.set_text(
                "Changing runlevel %s (current runlevel)" % runlevel)

gladepath = os.path.dirname(__file__)

def main():
    mainWindow = gtk.Window()
    mainWindow.connect("delete_event", gtk.main_quit)
    vbox = gtk.VBox(spacing=6)

    # service_name = 'cvs'
    service_name = 'nfs'

    status = ServiceStatus(service_name)
    serviceControl = ServiceControlToolbar(service_name, False)
    serviceMenu = ServiceMenu(service_name)
    mainWindow.add(vbox)
    menubar = gtk.MenuBar()
    menubar.append(serviceMenu.widget)
    vbox.add(menubar)
    vbox.add(serviceControl.widget)
    vbox.add(ServiceControlButtons(service_name).widget)
    vbox.add(status.widget)
    vbox.show_all()
    mainWindow.show()

    gtk.main()


if __name__ == "__main__":
    main ()
