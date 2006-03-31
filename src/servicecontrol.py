#!/bin/env python

import gtk, sys, os

from servicemethods import *

# XXX I18N!!!!! XXX

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

    def __init__(self):
        # Get icons
        self._redlight = gtk.gdk.pixbuf_new_from_file(
            "/usr/share/system-config-services/red.png")
        self._yellowlight = gtk.gdk.pixbuf_new_from_file(
            "/usr/share/system-config-services/yellow.png")
        self._greenlight = gtk.gdk.pixbuf_new_from_file(
            "/usr/share/system-config-services/green.png")
        self._nolight = gtk.gdk.pixbuf_new_from_file(
            "/usr/share/system-config-services/off.png")
        
    def _setState(self):
        status = self.service.status

        if status == RUNNING:
            if self.service.is_dirty():
                self.imgStatus.set_from_pixbuf(self._yellowlight)
            else:
                self.imgStatus.set_from_pixbuf(self._greenlight)
        elif status == ERROR:
            self.imgStatus.set_from_pixbuf(self._redlight)
        else:
            self.imgStatus.set_from_pixbuf(self._nolight)
        self.lblStatus.set_text(self.service.status_message)

    def on_servicestatus_show(self, widget):
        self._setState()
    

class ServiceControlBase:

    def __init__(self, service_name):
        self.uicallback = idle_func
        self.services = Services(idle_func)
        self.services.get_service_lists(service_name)
        self.service = self.services[service_name]

        self.statuswidget = None
        
    # ----------        

    def set_dirty(self, on):
        self._dirty = on

    def _setStart(self, on):
        if on:
            icon = gtk.image_new_from_icon_name("reload", 1)
            self.btnReStart.set_image(icon)
            icon.show()
            self.btnReStart.set_label("Restart")
            self.btnStop.set_sensitive(True)
        else:
            icon = gtk.image_new_from_icon_name("forward", 1)
            self.btnReStart.set_image(icon)
            self.btnReStart.set_label("Start")
            icon.show()
            self.btnStop.set_sensitive(False)

    def _setState(self):
        self._setStart(self.service.status==RUNNING)
        self._setRunlevelStatus()
        if self.statuswidget:
            self.statuswidget._setState()
            
    def _setRunlevelStatus(self):
        if self.service.is_default():
            on = self.service.is_default_on()
            self.btnEnable.set_sensitive(not on)
            self.btnDisable.set_sensitive(on)
        else:
            self.btnEnable.set_sensitive(False)
            self.btnDisable.set_sensitive(False)

    def on_servicetab_show(self, widget):
        self._setState()

    def on_btnReStart_clicked(self, button):
        if self.service.status == RUNNING:
            self.service.action('restart')
        else:
            self.service.action('start')
        self._setState()
        
    def on_btnStop_clicked(self, button):
        self.service.action('stop')
        self._setState()

    def on_btnRunlevels_clicked(self, button):
        err, message = getstatusoutput("/usr/bin/system-config-services",
                                       self.uicallback)
        self._setState()

    def on_btnEnable_clicked(self, button):
        self.service.set(True)
        self.service.save_changes()
        self._setState()

    def on_btnDisable_clicked(self, button):
        self.service.set(False)
        self.service.save_changes()        
        self._setState()

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

class ServiceControlHBox(ServiceControlBase, gtk.HBox):
    #XXX DOES NOT WORK YET!
    def __init__(self): # XXX

        ServiceControlBase.__init__(self) #XXX

        #  Setup GUI

        gtk.HBox.__init__(self, homogeneous=False)

        vbox = gtk.VBox()
        vbox.show()
        self.stateIcon = gtk.Image()
        #self.stateIcon.set_from_f("red.png")
        self.stateIcon.show()
        vbox.add(self.stateIcon)

        label = gtk.Label("Status")
        label.show()
        vbox.add(label)
        
        self.pack_start(vbox, expand=False)


        
        self.toolbar = gtk.Toolbar()
           
        self._addSeperator()
        self.btnStartStop = self._addButton("Start", "forward",
                                            self._startStop)
        self.btnReload = self._addButton("Restart", "reload", self._restart)
        self.btnReload.set_sensitive(False)
        self._addSeperator()

        if runlevel_buttons:

            self.btnRunlevel = { }

            for runlevel in [5, 4, 3, 2]:
                if self.serviceMethods.check_if_on(service_name, runlevel):
                    icon = "ok"
                else:
                    icon = "no"
                btn = self._addButton("Runlevel %d" % runlevel, icon,
                                      self._toggleRunlevel, runlevel)
                self.btnRunlevel[runlevel] = btn
        else:
            self._addButton("Runlevels", "configure", self.openServicesTool)


        self.add(self.toolbar)
        self.toolbar.show()

        self.set_size_request(-1, 53)
        self._setState(self.serviceState)

    def _addButton(self, label, icon, callback, data=None, disabled=False):
        btn = gtk.ToolButton(label)

        btn.set_label(label)
        
        icon = gtk.image_new_from_icon_name(icon, 2)
        btn.set_icon_widget(icon)
        icon.show()

        if data is not None:
            btn.connect("clicked", callback, data)
        else:
            btn.connect("clicked", callback)
            
        self.toolbar.add(btn)
        btn.show()

        return btn

    def _addSeperator(self):
        seperator = gtk.SeparatorToolItem() 
        self.toolbar.add(seperator)
        seperator.show()


class ServiceControlVBox(ServiceControlBase, gtk.VBox):
    #XXX DOES NOT WORK YET!
    pass

class ServiceTab(ServiceControlBase, GladeWidget):
    """Widget for controlling a service"""
    def __init__(self, service_name):
        ServiceControlBase.__init__(self, service_name)
        self.xml = gtk.glade.XML(
            os.path.join(gladepath, "servicetab.glade"), root="servicetab")

        # set as attributes
        self.getWidgets('btnEnable', 'btnDisable', 'btnRunlevels',
                        'lblRunlevel', 'lblEditingRunlevels',
                        'btnReStart', 'btnStop',
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

class ServiceStatus(ServiceStatusBase, GladeWidget):
    """Status bar widget"""
    def __init__(self):

        ServiceStatusBase.__init__(self)
        
        self.xml = gtk.glade.XML(
            os.path.join(gladepath, "servicetab.glade"), root="servicestatus")
        self.getWidgets('servicestatus', 'lblStatus', 'imgStatus')
        self.widget = self.servicestatus
        self.xml.signal_autoconnect(self)

gladepath = os.path.dirname(__file__)

def main():
    mainWindow = gtk.Window()
    mainWindow.connect("delete_event", gtk.main_quit)

    serviceControl = ServiceControl("nfs", runlevel_buttons=False)
    mainWindow.add(serviceControl)
    
    mainWindow.show()
    serviceControl.show()

    gtk.main()


if __name__ == "__main__":
    main ()
