#!/bin/env python

import gtk.glade, sys, os
from rhpl.translate import _
from servicemethods import *
from gtk_chooserbutton import ChooserButton, ToolChooserButton

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


def stopRecursion(func):
    def f(self, *args):
        if not hasattr(self, '_no_recursion'):
            self._no_recursion = False
        if self._no_recursion:
            return
        self._no_recursion = True
        result = func(self, *args)
        self._no_recursion = False
        return result

    f.__name = func.__name__
    f.__doc__ = func.__doc__
    f.__dict__.update(func.__dict__)

    return f

class GladeWidget:

    status_icons = {
        UNKNOWN : 'gtk-dialog-warning',
        RUNNING : 'gtk-execute',
        STOPPED : 'gtk-stop',
        ERROR : 'gtk-dialog-error',
        }

    def getWidgets(self, *names, **kw):
        xml = kw.get('xml', self.xml)
        for name in names:
            widget = xml.get_widget(name)
            if widget is None and kw.get('strict', True):
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

    @stopRecursion
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

    disable_non_default = True

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
            if hasattr(self, 'separator1'):
                self.separator1.hide()
                self.separator1.set_no_show_all(True)

        if not configure:
            if hasattr(self, 'separator2'):
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
        if hasattr(self, 'Enable2'):
            self.Enable2.set_sensitive(on)
        self.Disable.set_sensitive(on)
        if hasattr(self, 'Disable2'):
            self.Disable2.set_sensitive(on)

    def _setRunlevels(self):
        if self.service.is_xinetd_service():
            return
        runlevels = self.service.get_runlevels()
        for nr in [2, 3, 4, 5]:
            if hasattr(self, 'runlevel_%i' % nr):
                getattr(self, 'runlevel_%i' % nr).set_active(runlevels[nr])

    @stopRecursion
    def _setState(self):
        self._setExists()
        self._setRunlevels()
        if self.service.exists():
            self._setStart(self.service.status==RUNNING)
            self._setRunlevelStatus()
            
    def _setRunlevelStatus(self):
        buttons = isinstance(self.Enable, (gtk.ToolButton, gtk.Button))
        if self.service.is_default():
            on = self.service.is_default_on()
            self.Enable.set_sensitive(not on)
            if hasattr(self, 'Enable2'):
                self.Enable2.set_sensitive(not on)
            self.Disable.set_sensitive(on)
            if hasattr(self, 'Disable2'):
                self.Disable2.set_sensitive(on)
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
            self.Enable.set_sensitive(False)
            if hasattr(self, 'Enable2'):
                self.Enable2.set_sensitive(False)
            self.Disable.set_sensitive(self.disable_non_default)
            if hasattr(self, 'Disable2'):
                self.Disable2.set_sensitive(True)
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
        if hasattr(self, 'StartButton'):
            self.StartButton.set_text('Starting')
            self.StartButton.set_stock_icon('gtk-media-play')
        self.service.action('start')
        self._setState()

    def on_Restart_clicked(self, button):
        if hasattr(self, 'StartButton'):
            self.StartButton.set_text('Starting')
            self.StartButton.set_stock_icon('gtk-refresh')
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
        if hasattr(button,  'get_active') and not button.get_active():
            return
        self.service.set(True)
        self.service.save_changes()
        self._setState()

    def on_Disable_clicked(self, button):
        if hasattr(button,  'get_active') and not button.get_active():
            return
        self.service.set(False)
        self.service.save_changes()        
        self._setState()

    def on_Enable_All_clicked(self, widget):
        self.service.set_in_runlevels(True, [2, 3, 4, 5])
        self.service.save_changes()
        self._setState()

    @stopRecursion
    def on_Runlevel_toggled(self, widget):
        for nr in [2, 3, 4, 5]:
            if  getattr(self, 'runlevel_%i' % nr) is widget:
                print "XXX", widget, widget.get_active()
                self.service.set_in_runlevels(widget.get_active(), nr)
                self.service.save_changes()
                break

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

    def update(self, service, userdata=None):
        self._setState()

class ExtendedServiceControl(ServiceControlBase, GladeWidget):
    widget_name = 'ServiceControlButtons'

    def __init__(self, service_name, configure=False):
        self.xml = gtk.glade.XML(os.path.join(gladepath, "servicetab.glade"), root=self.widget_name)
        self.xml2 =  gtk.glade.XML(os.path.join(gladepath, "servicetab.glade"), root='menuService')
        self.xml3 =  gtk.glade.XML(os.path.join(gladepath, "servicetab.glade"), root='menuStartStop')

        self.xml.signal_autoconnect(self)
        self.xml2.signal_autoconnect(self)
        self.xml3.signal_autoconnect(self)

        self.widget = self.xml.get_widget(self.widget_name)
        self.getWidgets('ServiceName', 'EnableService', 'StartService', 'Configure')
        self.getWidgets('menuService', 'Enable', 'Disable', 'Enable2', 'Enable_All', 'Disable2', 
                        'runlevel_2', 'runlevel_3', 'runlevel_4', 'runlevel_5', xml=self.xml2)
        self.getWidgets('menuStartStop', 'Start', 'Stop', 'Restart', xml=self.xml3)
        
        if isinstance(self.EnableService, gtk.MenuToolButton):
            self.EnableButton = ToolChooserButton(self.EnableService)
            self.EnableButton.set_menu(self.menuService)
            self.StartButton = ToolChooserButton(self.StartService)
            self.StartButton.set_menu(self.menuStartStop)
        else:
            self.EnableButton = ChooserButton(self.EnableService)
            self.EnableButton.set_menu(self.menuService)
            self.StartButton = ChooserButton(self.StartService)
            self.StartButton.set_menu(self.menuStartStop)

        ServiceControlBase.__init__(self, service_name, configure)

        self.ServiceName.set_text(self.ServiceName.get_text() % service_name)

        default_levels = self.service.get_default_runlevels()
        for nr in [2, 3, 4, 5]:
            label = getattr(self, 'runlevel_%s' % nr).get_child()
            if nr in default_levels:
                label.set_text('Runlevel %s (default)' % nr)
            else:
                label.set_text('Runlevel %s' % nr)

        self.service.subscribe(self.update)
        self._setState()

    @stopRecursion
    def _setState(self):
        self._setExists()
        self._setRunlevels()
        if self.service.exists():
            self.StartButton.set_text(status_text[self.service.status])
            self.StartButton.set_stock_icon(self.status_icons[self.service.status])
            self._setStart(self.service.status==RUNNING)
            if not self.service.is_default():
                self.EnableButton.set_text('Customized')
                self.EnableButton.set_stock_icon('gtk-preferences')
            elif self.service.is_default_on():
                self.EnableButton.set_text('Enabled')
                self.EnableButton.set_stock_icon('gtk-yes')
            else:
                self.EnableButton.set_text('Disabled')
                self.EnableButton.set_stock_icon('gtk-no')

            self._setRunlevelStatus()
        
class ServiceControlToolbar(ServiceControlBase):
    widget_name = "ServiceControlToolbar"

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
        
class ServiceControlButtons(ExtendedServiceControl):
    widget_name = "ServiceControlButtons"

class ServiceControlToolbar(ExtendedServiceControl):
    widget_name = "ServiceControlToolbar"

class ServiceMenu(ServiceControlWidget):
    widget_name = "ServiceMenu"

    disable_non_default = False

    def __init__(self, service_name, configure=False):
        self.xml = gtk.glade.XML(os.path.join(gladepath, "servicetab.glade"), root=self.widget_name)

        self.xml.signal_autoconnect(self)

        self.widget = self.xml.get_widget(self.widget_name)
        self.getWidgets('Enable', 'Disable', 'Customize', 'ServiceMenu_menu', 'separator1',
                        'Start', 'Stop', 'Restart', 'separator2', 'Configure', 
                        'Enable2', 'Enable_All', 'Disable2', 
                        'runlevel_2', 'runlevel_3', 'runlevel_4', 'runlevel_5')
        
        ServiceControlBase.__init__(self, service_name, configure)

        self.widget.get_child().set_text(self.widget.get_child().get_text() % service_name)

        if self.service.is_xinetd_service():
            # self.Customize.set_sensitive(False)
            self.Customize.hide()
            self.Customize.set_no_show_all(True)

        default_levels = self.service.get_default_runlevels()
        for nr in [2, 3, 4, 5]:
            label = getattr(self, 'runlevel_%s' % nr).get_child()
            if nr in default_levels:
                label.set_text('Runlevel %s (default)' % nr)
            else:
                label.set_text('Runlevel %s' % nr)

        self.service.subscribe(self.update)
        self._setState()

        
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
    vbox = gtk.VBox(spacing=0)
    mainWindow.add(vbox)

    # service_name = 'cvs'
    service_name = 'nfs'

    menubar = gtk.MenuBar()
    menuitem = gtk.MenuItem('Services')
    menubar.append(menuitem)

    services = gtk.Menu()
    menuitem.set_submenu(services)

    serviceMenu = ServiceMenu(service_name)
    services.append(serviceMenu.widget)
    serviceMenu2 = ServiceMenu('tftp')
    services.append(serviceMenu2.widget)

    status = ServiceStatus(service_name)
    serviceControl = ServiceControlToolbar(service_name, False)

    vbox.add(menubar)
    vbox.add(serviceControl.widget)
    vbox.add(ServiceControlButtons(service_name).widget)
    vbox.add(status.widget)
    vbox.show_all()
    mainWindow.show()

    gtk.main()


if __name__ == "__main__":
    main ()
