import gettext
import gnome
import dnsdata 
from dnsdata import *
#import gnome.ui
import gtk
from gtk import FALSE
from gtk import TRUE
from copy import copy
import string
import os
#Columns for "a_treeview"
COLUMN_PIXBUF=0
COLUMN_TEXT=1
COLUMN_MAIL_XCHANGE=1
COLUMN_DATA=2
COLUMN_TEXT2=3
COLUMN_PRIORITY=3
COLUMN_HASH=4

##
## I18N stuff
##
_=gettext.gettext
gettext.bindtextdomain("bindconf", "/usr/share/locale")
gettext.textdomain("bindconf")

bindconf_dir = '/usr/share/bindconf'


#Columns for "bindconf_treeview"
COLUMN_PIXBUF=0
COLUMN_TEXT=1
COLUMN_DATA=2

#columns for "rev_zone_treeview", "fwd_zone_treeview"
COLUMN_TEXT2=3
COLUMN_HASH=4

def load_image(filename):
    if not os.path.exists(filename):
        filename = bindconf_dir + "/" + filename
    return gtk.gdk.pixbuf_new_from_file(filename)

image_a = load_image("address.png")
image_cname = load_image("cname.png")
image_ns = load_image("domain.png")
image_mx = load_image("mail.png")

def generic_error_dialog (message, parent_dialog, dialog_type=gtk.MESSAGE_WARNING, widget=None, page=0, broken_widget=None):
    dialog = gtk.MessageDialog (parent_dialog,
                                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                                dialog_type,
                                gtk.BUTTONS_OK,
                                message)
    if widget != None:
        if isinstance (widget, gtk.CList):
            widget.select_row (page, 0)
        elif isinstance (widget, gtk.Notebook):
            widget.set_page (page)

    if broken_widget != None:
        broken_widget.grab_focus ()
#        if isinstance (broken_widget, gtk.Entry):
            ##FIXME: supposedly deprecated?
#            broken_widget.select_region (0, -1)
    dialog.run ()
    dialog.destroy ()

class AProxy:
    ORDER='B'
    def __init__ (self, a=None):
        if a:
            self.host = a.getHost ()
            self.ip = a.getIp ()

    def get_str (self):
        return self.host + ':' + self.ip

    def get_hash (self):
        return AProxy.ORDER + self.host

    def get_pix (self):
        return image_a

    def add_mx (self, button, fwdzone, xml):
        tree_view = xml.get_widget ('a_treeview')
        mx = MXProxy ()
        if mx.run_add_dialog (fwdzone, xml, xml.get_widget ('a_dialog'),self.host):
            model = tree_view.get_model ()
            iter=model.append()
            model.set (iter,
                       COLUMN_PIXBUF,mx.get_pix(),
                       COLUMN_MAIL_XCHANGE,mx.host,
                       COLUMN_PRIORITY, str (mx.priority),
                       COLUMN_HASH, mx.get_priority_hash(),
                       COLUMN_DATA,mx)
            tree_view.get_selection ().select_iter (iter)

    def edit_mx (self, button, fwdzone, xml):
        tree_view = xml.get_widget ('a_treeview')
        selected = tree_view.get_selection().get_selected ()
        if selected != None:
            (model, iter) = selected
            mx = model.get_value (iter, COLUMN_DATA)
            mx.run_edit_dialog (fwdzone, xml, xml.get_widget ('a_dialog'))
            model.set (iter,
                       COLUMN_PIXBUF,mx.get_pix (),
                       COLUMN_MAIL_XCHANGE,mx.host,
                       COLUMN_PRIORITY, str (mx.priority),
                       COLUMN_HASH, mx.get_priority_hash())
                       
    def delete_mx (self, button, xml):
        tree_view = xml.get_widget ('a_treeview')
        result = tree_view.get_selection().get_selected ()
        if result != None:
            (model, iter) = result
            path = model.get_path (iter)
            model.remove (iter)
            try:
                iter = model.get_iter (path)
            except:
                pass
            if iter == None:
                path = (0)
            tree_view.get_selection().select_path (path)

    def run_edit_dialog (self, fwdzone, xml,parent):
        dialog = xml.get_widget ('a_dialog')
        dialog.set_transient_for (parent)
        host_entry = xml.get_widget ('a_host_entry')
        ip_entry = xml.get_widget ('a_ip_entry')
        label = xml.get_widget ('a_dialog_label')
        tree_view = xml.get_widget ('a_treeview')

        add_button = xml.get_widget ('a_add_button')
        edit_button = xml.get_widget ('a_edit_button')
        delete_button = xml.get_widget ('a_delete_button')

        add_id = add_button.connect ('clicked', self.add_mx, fwdzone, xml)
        edit_id = edit_button.connect ('clicked', self.edit_mx, fwdzone, xml)
        delete_id = delete_button.connect ('clicked', self.delete_mx, xml)

        host_entry.set_text (self.host)
        ip_entry.set_text (self.ip)
        host_entry.grab_focus ()
        label.set_text ('.' + fwdzone.name)
        edit_button.set_sensitive (FALSE)
        delete_button.set_sensitive (FALSE)

        model = tree_view.get_model()
        model.clear ()
        for mx in fwdzone.mx:
            if mx.applies_to == self.host:
                iter = model.append()
                model.set (iter,
                           COLUMN_PIXBUF,mx.get_pix (),
                           COLUMN_MAIL_XCHANGE,mx.host,
                           COLUMN_PRIORITY, str (mx.priority),
                           COLUMN_HASH, mx.get_priority_hash(),
                           COLUMN_DATA,mx)

        tree_view.get_selection ().select_path ((0,))
        while 1:
            button = dialog.run ()
            if button != gtk.RESPONSE_OK:
                dialog.hide ()
                add_button.disconnect (add_id)
                edit_button.disconnect (edit_id)
                delete_button.disconnect (delete_id)
                return button

            host = host_entry.get_text ()
            ip = ip_entry.get_text ()

            try:
                ag = dnsdata.A()
                brw = host_entry
                ag.testHost(host)
                brw = ip_entry
                ag.testIp(ip)
            except TestError, e:
                generic_error_dialog (e.args, dialog, broken_widget=brw)
                continue

#              try:
#                  fwdzone.zone.test()
#              except TestError, e:
#                  def callback (*args):
#                      pass
#                  qa = gnome.ui.GnomeQuestionDialog (_("The following error occured due to host %s\n%s\nAre you sure you want to add this host?") % (host, e.args), callback, dialog)
#                  button = qa.run ()
#                  if button != 0:
#                      continue

            dialog.hide ()
            break

        dellist = []
        for mx in fwdzone.mx:
            if mx.applies_to == self.host:
                dellist.append (mx)

        for mx in dellist:
            fwdzone.mx.remove (mx)

        iter = model.get_iter_first ()
        def foreach_func (model, path, iter, text):
            mx = model.get_value (iter, COLUMN_DATA)
            mx.applies_to = host
            fwdzone.mx.append (mx)

        model.foreach (foreach_func, None)

        self.host = host
        self.ip = ip

        add_button.disconnect (add_id)
        edit_button.disconnect (edit_id)
        delete_button.disconnect (delete_id)
        return button

    def check(self):
        ag = dnsdata.A()
        ag.testHost(self.host)
        ag.testIp(self.ip)

class CNAMEProxy:
    ORDER='C'
    def __init__ (self, cname=None):
        if cname:
            self.alias = cname.getAlias ()
            self.host = cname.getHost ()

    def get_str (self):
        return self.host + _(" aliased to ") + self.alias

    def get_hash (self):
        return CNAMEProxy.ORDER + self.alias

    def get_pix (self):
        return image_cname

    def run_edit_dialog (self, fwdzone, xml, parent):
        dialog = xml.get_widget ('cname_dialog')
        dialog.set_transient_for (parent)
        host_entry = xml.get_widget ('cname_host_entry')
        alias_entry = xml.get_widget ('cname_alias_entry')
        label = xml.get_widget ('cname_label')

        host_entry.set_text (self.host)
        alias_entry.set_text (self.alias)
        host_entry.grab_focus ()
        label.set_text ('.' + fwdzone.name)

        while 1:
            button = dialog.run ()
            if button != gtk.RESPONSE_OK:
                dialog.hide ()
                return button
            host = host_entry.get_text ()
            alias = alias_entry.get_text ()

            if host == "":
                generic_error_dialog (_("You must enter a host name."), dialog, broken_widget=host_entry)
                continue
            if alias == "":
                generic_error_dialog (_("You must enter an alias."), dialog, broken_widget=alias_entry)
                continue

            try:
                cg = dnsdata.CNAME()
                brw = host_entry
                cg.testHost(host)
                brw = alias_entry
                cg.testAlias(alias)
            except TestError, e:
                generic_error_dialog (e.args, dialog, broken_widget=brw)
                continue

            try:
                for cname in fwdzone.cname:
                    if cname == self:
                        continue
                    if cname.alias == alias:
                        raise 'Duplicate'
            except 'Duplicate':
                generic_error_dialog (_("An alias with this name already exists."), dialog, broken_widget=alias_entry)
                continue
            dialog.hide ()
            break
        self.host = host
        self.alias = alias
        return button

    def check(self):
        ag = dnsdata.CNAME()
        ag.testHost(self.host)
        ag.testAlias(self.alias)

class MXProxy:
    ORDER='D'
    def __init__ (self, mx=None):
        if mx:
            self.host = mx.getHost ()
            self.priority = mx.getPriority ()
            self.applies_to = mx.getAppliesTo ()
        else:
            self.applies_to = "@"

    def get_str (self):
        return self.host + _(" at priority ") + str (self.priority)

    def get_hash (self):
        return MXProxy.ORDER + self.host

    def get_priority_hash (self):
        str = "%8d" % self.priority
        return re.sub (' ', '0', str) + self.host

    def get_pix (self):
        return image_mx

    def run_edit_dialog (self, fwdzone, xml, parent, name=None):
        return self.run_dialog (fwdzone, xml, parent, name, TRUE)

    def run_add_dialog (self, fwdzone, xml, parent, name=None):
        return self.run_dialog (fwdzone, xml,parent, name, FALSE)

    def run_dialog (self, fwdzone, xml, parent,name, edit):
        dialog = xml.get_widget ('mx_dialog')
        dialog.set_transient_for (parent)
        host_entry = xml.get_widget ('mx_host_entry')
        priority_entry = xml.get_widget ('mx_priority_entry')
        label = xml.get_widget ('mx_label')

        if name:
            label.set_text (_("Mail Exchanger for %s") % (name + '.' + fwdzone.name))
        else:
            label.set_text (_("Mail Exchanger for %s") % fwdzone.name)

        if edit:
            host_entry.set_text (self.host)
            priority_entry.set_text (str (self.priority))
            dialog.set_title (_("Edit Mail Exchanger"))
        else:
            host_entry.set_text ("")
            priority_entry.set_text ("")
            dialog.set_title (_("Add a Mail Exchanger"))

        host_entry.grab_focus ()

        while 1:
            button = dialog.run ()
            if button != gtk.RESPONSE_OK:
                dialog.hide ()
                return button
            host = host_entry.get_text ()
            priority = priority_entry.get_text ()

            if host == "":
                generic_error_dialog (_("You must enter a host name."), dialog, broken_widget=host_entry)
                continue
            if priority == "":
                generic_error_dialog (_("You must enter an priority."), dialog, broken_widget=priority_entry)
                continue

            try:
                mxg = dnsdata.MX()
                brw = host_entry
                mxg.testHost(host)
                brw = priority_entry
                mxg.testPriority(int(priority))                
            except TestError, e:
                generic_error_dialog (e.args, dialog, broken_widget=brw)
                continue

            dialog.hide ()
            break
        self.host = host
        self.priority = int (priority)
        return button
    def check(self):
        dnsdata.MX().testHost(self.host)

class NSProxy:
    ORDER = 'Z'
    def __init__ (self, ns=None):
        if ns:
            self.host = ns.getHost ()
            self.applies_to = ns.getAppliesTo ()

    def get_str (self):
        return str (self.applies_to) + _(" served by ") + str(self.host)

    def get_hash (self):
        return NSProxy.ORDER + self.host

    def get_pix (self):
        return image_ns

    def run_dialog (self, name, xml, edit, zone, parent, full_ns_host = FALSE):
        dialog = xml.get_widget ('ns_dialog')
        dialog.set_transient_for (parent)
        host_entry = xml.get_widget ('ns_host_entry')
        applies_to_entry = xml.get_widget ('ns_applies_to_entry')
        label = xml.get_widget ('ns_label')

        if edit:
            host_entry.set_text (self.host)
            applies_to_entry.set_text (self.applies_to)
        else:
            host_entry.set_text ('')
            applies_to_entry.set_text ('')
        host_entry.grab_focus ()
        if zone:
            applies_to_entry.hide ()
            label.set_text (name)
        else:
            applies_to_entry.show ()
            label.set_text ('.' + name)

        while 1:
            button = dialog.run ()
            if button != gtk.RESPONSE_OK:
                dialog.hide ()
                return button

            host = host_entry.get_text ()
            applies_to = applies_to_entry.get_text ()

            if host == "":
                generic_error_dialog (_("You must enter a host name."), dialog, broken_widget=host_entry)
                continue
            if applies_to == "" and not zone:
                generic_error_dialog (_("You must enter a resolution address."), dialog, broken_widget=applies_to_entry)
                continue

            try:
                nsg = dnsdata.NS()
                brw = host_entry
                nsg.testHost(host)
                if full_ns_host and (not ((len(host) > 1) and host[-1] == '.')):
                    raise TestError, _("NS hostname `") + host + _("' has no . at the end. You must use a full hostname.")
                if not zone:
                    brw = applies_to_entry
                    nsg.testAppliesTo(applies_to)
            except TestError, e:
                generic_error_dialog (e.args, dialog, broken_widget=brw)
                continue

            dialog.hide ()
            break
        self.host = host

        if zone:
            self.applies_to = '@'
        else:
            self.applies_to = applies_to
        return button

    def run_edit_dialog (self, fwdzone, xml, parent, zone=FALSE):
        return self.run_dialog (fwdzone.name, xml, TRUE, zone, parent)

    def run_add_dialog (self, fwdzone, xml, parent, zone=FALSE):
        return self.run_dialog (fwdzone.name, xml, FALSE, zone, parent)

    def check(self):
        nsg = dnsdata.NS()
        nsg.testHost(self.host)
        nsg.testAppliesTo(self.applies_to)

class FwdZone:
    ORDER='A'
    def __init__(self, zone, xml):
        self.zone = zone
        self.xml = xml
        self.hydrating = FALSE
        if not hasattr(self.zone, 'dirty'):
	    self.zone.dirty = FALSE
	self.dirty = self.zone.dirty

        #slurp from the zone
        soa = zone.getSOA ()

        self.name = zone.getName ()
        self.file = zone.getFile ()

        self.contact = soa.getContact ()
        self.serial = soa.getSerial ()
        self.refresh = soa.getRefresh ()
        self.retry = soa.getRetry ()
        self.expire = soa.getExpire ()
        self.minimum = soa.getMinimum ()
        self.pns = soa.getPNS()
        
        self.ns = []
        nslist = zone.getNSList ()
        if nslist:
            for i in xrange (0, nslist.getNumNS ()):
                ns = nslist.getNS (i)
                proxy = NSProxy (ns)
                self.ns.append (proxy)

        self.mx = []
        mxlist = zone.getMXList ()
        if mxlist:
            for i in xrange (0, mxlist.getNumMX ()):
                mx = mxlist.getMX (i)
                proxy = MXProxy (mx)
                self.mx.append (proxy)

        self.cname = []
        cnamelist = zone.getCNAMEList ()
        if cnamelist:
            for i in xrange (0, cnamelist.getNumCNAME ()):
                cname = cnamelist.getCNAME (i)
                proxy = CNAMEProxy (cname)
                self.cname.append (proxy)

        self.a = []
        alist = zone.getAList ()
        if alist:
            for i in xrange (0, alist.getNumA ()):
                a = alist.getA (i)
                proxy = AProxy (a)
                self.a.append (proxy)

    def get_str (self):
        return self.name

    def get_pix (self):
        return None

    def get_hash (self):
        return FwdZone.ORDER

    def hydrate (self):
        self.hydrating = TRUE
        xml = self.xml
        dialog = xml.get_widget ('fwd_master_dialog')
        name_entry = xml.get_widget ('fwd_zone_name_entry')
        contact_entry = xml.get_widget ('fwd_zone_contact_entry')
        serial_entry = xml.get_widget ('fwd_zone_serial_entry')
        tree_view = xml.get_widget ('fwd_zone_treeview')
        model = tree_view.get_model()
        self.pns_entry = xml.get_widget ('fwd_zone_pns_entry')
        name_entry.set_text (self.name)
        contact_entry.set_text (self.contact)
        serial_entry.set_text (str (self.serial))
        self.pns_entry.set_text(self.pns)
        self.hydrating = FALSE

        model.clear ()
        iter = model.append ()
        model.set (iter,
                   COLUMN_TEXT, self.get_str(),
                   COLUMN_HASH, self.get_hash(),
                   COLUMN_DATA, self)

        for a in self.a:
            if a.host == '@':
                continue
            iter = model.append ()
            model.set (iter,
                       COLUMN_PIXBUF, image_a,
                       COLUMN_TEXT, a.get_str(),
                       COLUMN_TEXT2, '',
                       COLUMN_HASH, a.get_hash(),
                       COLUMN_DATA, a)
        for cname in self.cname:
            iter = model.append ()
            model.set (iter,
                       COLUMN_PIXBUF, image_cname,
                       COLUMN_TEXT, cname.get_str(),
                       COLUMN_TEXT2, '',
                       COLUMN_HASH, cname.get_hash(),
                       COLUMN_DATA, cname)
        for ns in self.ns:
            if ns.applies_to == '@':
                continue
            iter = model.append ()
            model.set (iter,
                       COLUMN_PIXBUF, image_ns,
                       COLUMN_TEXT, ns.get_str(),
                       COLUMN_TEXT2, '',
                       COLUMN_HASH, ns.get_hash(),
                       COLUMN_DATA, ns)

    def hydrate_soa (self):
        self.hydrating = TRUE
        xml = self.xml
        xml.get_widget ('soa_refresh_entry').set_text (str (self.refresh))
        xml.get_widget ('soa_retry_entry').set_text (str (self.retry))
        xml.get_widget ('soa_expire_entry').set_text (str (self.expire))
        xml.get_widget ('soa_minimum_entry').set_text (str (self.minimum))
        self.hydrating = FALSE

    def dehydrate_soa (self):
        xml = self.xml
        def my_int (str):
            try:
                i = int (str)
                return i
            except:
                return 0

        self.refresh = my_int (xml.get_widget ('soa_refresh_entry').get_text ())
        self.retry = my_int (xml.get_widget ('soa_retry_entry').get_text ())
        self.expire = my_int (xml.get_widget ('soa_expire_entry').get_text ())
        self.minimum = my_int (xml.get_widget ('soa_minimum_entry').get_text ())

    def set_name (self, name):
        xml = self.xml
        self.name = name
        self.set_dirty ()
        tree_view= xml.get_widget ('fwd_zone_treeview')
        model = tree_view.get_model ()
        iter = model.get_iter_first ()
        if iter == None:
            iter = model.append ()
        model.set_value (iter, COLUMN_TEXT, self.name)
        xml.get_widget ('fwd_zone_file_entry').set_text (self.name + '.zone')

    def set_dirty (self):
        if self.hydrating: return
        if self.dirty: return
        self.dirty = TRUE

    def check(self):
        self.zone.testName(self.name)
        self.zone.testFile(self.file)
        #test_soa_values
        soa = self.zone.getSOA()
        soa.testPNS(self.pns_entry.get_text())
        if self.refresh < self.retry:
            raise TestError, _("SOA Refresh value should be bigger than Retry")
        soa.testSerial(self.serial)
        soa.testRefresh(self.refresh)
        soa.testRetry(self.retry)
        soa.testExpire(self.expire)
        soa.testMinimum(self.minimum)

        #test_a_list
        for I in self.a:
            I.check()
        #test_ns_list
        for I in self.ns:
            I.check()
        #test_cname_list
        for I in self.cname:
            I.check()
        #test_mx_list
        for I in self.mx:
            I.check()
        if len (self.ns) < 1:
            raise TestError, _("Forward zone `") + self.name + _("' must list at least one name server")

    def dehydrate (self):
        for I in self.ns + self.mx + self.cname + self.a:
            if hasattr(I, 'dirty') and I.dirty:
                self.dirty = TRUE
        
	if self.dirty and not self.zone.dirty:
        	self.serial = self.serial+1
                self.zone.dirty = TRUE
	        self.xml.get_widget ('fwd_zone_serial_entry').set_text (str (self.serial))

        self.name = self.xml.get_widget ('fwd_zone_name_entry').get_text ()
        self.file = self.xml.get_widget ('fwd_zone_file_entry').get_text ()
        self.contact = self.xml.get_widget ('fwd_zone_contact_entry').get_text()
        self.pns = self.pns_entry.get_text()
        
        soa = self.zone.getSOA ()
        self.zone.setName (self.name)
        self.zone.setFile (self.file)
        soa.setContact (self.contact)
        soa.setSerial (self.serial)
        soa.setRefresh (self.refresh)
        soa.setRetry (self.retry)
        soa.setExpire (self.expire)
        soa.setMinimum (self.minimum)
        soa.setPNS(self.pns)
        
        self.zone.delNSList ()
        if len (self.ns) > 0:
            nslist = self.zone.createNSList ()
            for ns in self.ns:
                nsg = nslist.addNS ()
                nsg.setHost (ns.host)
                nsg.setAppliesTo (ns.applies_to)

        self.zone.delMXList ()
        if len (self.mx) > 0:
            mxlist = self.zone.createMXList ()
            for mx in self.mx:
                mxg = mxlist.addMX ()
                mxg.setHost (mx.host)
                mxg.setAppliesTo (mx.applies_to)
                mxg.setPriority (mx.priority)

        self.zone.delCNAMEList ()
        if len (self.cname) > 0:
            cnamelist = self.zone.createCNAMEList ()
            for cname in self.cname:
                cnameg = cnamelist.addCNAME ()
                cnameg.setHost (cname.host)
                cnameg.setAlias (cname.alias)

        self.zone.delAList ()
        if len (self.a) > 0:
            alist = self.zone.createAList ()
            for a in self.a:
                ag = alist.addA ()
                ag.setHost (a.host)
                ag.setIp (a.ip)

#####
    def run_edit_dialog (self, fwdzone, xml,parent):
        dialog = xml.get_widget ('zone_dialog')
        dialog.set_transient_for (parent)
        entry = xml.get_widget ('zone_address_entry')

        dialog.set_title (_("Settings for %s") % self.name)

        tmp = ''
        first = TRUE
        for a in self.a:
            if a.host == '@':
                if first:
                    tmp = a.ip
                    first = FALSE
                else:
                    tmp = tmp + " " + a.ip
        entry.set_text (tmp)

        ns_tree_view = xml.get_widget ('zone_ns_treeview')
        ns_model = ns_tree_view.get_model()
        ns_model.clear ()
        for ns in self.ns:
            if ns.applies_to != '@':
                continue
            iter = ns_model.append ()
            ns_model.set (iter,
                          COLUMN_PIXBUF,ns.get_pix (),
                          COLUMN_TEXT,ns.host,
                          COLUMN_TEXT2, '',
                          COLUMN_HASH, ns.get_hash(),
                          COLUMN_DATA,ns)

        tree_view = xml.get_widget ('zone_mx_treeview')
        model = tree_view.get_model()
        model.clear ()
        for mx in self.mx:
            if mx.applies_to != '@':
                continue
            iter = model.append ()
            model.set (iter,
                       COLUMN_PIXBUF,mx.get_pix (),
                       COLUMN_MAIL_XCHANGE,mx.host,
                       COLUMN_PRIORITY, str (mx.priority),
                       COLUMN_HASH, mx.get_priority_hash(),
                       COLUMN_DATA,mx)

        while 1:
            button = dialog.run ()
            if button != gtk.RESPONSE_OK:
                dialog.hide ()
                return button
            #FIXME: put checks in here.
            break

        dialog.hide ()

        dellist = []
        for ns in self.ns:
            if ns.applies_to == '@':
                dellist.append (ns)

        for ns in dellist:
            self.ns.remove (ns)

        dellist = []
        for a in self.a:
            if a.host == '@':
                dellist.append (a)

        for a in dellist:
            self.a.remove (a)

        dellist = []
        for mx in self.mx:
            if mx.applies_to == '@':
                dellist.append (mx)

        for mx in dellist:
            self.mx.remove (mx)

        ns_tree_view = xml.get_widget ('zone_ns_treeview')
        ns_model = ns_tree_view.get_model ()
        iter = ns_model.get_iter_first ()
        def foreach_ns_func (model, path, iter, text):
            ns = model.get_value (iter, COLUMN_DATA)
            ns.applies_to = '@'
            fwdzone.ns.append (ns)

        ns_model.foreach (foreach_ns_func, None)

        tree_view = xml.get_widget ('zone_mx_treeview')
        model = tree_view.get_model ()
        iter = model.get_iter_first ()
        def foreach_func (model, path, iter, text):
            mx = model.get_value (iter, COLUMN_DATA)
            mx.applies_to = '@'
            fwdzone.mx.append (mx)

        model.foreach (foreach_func, None)

        tmp = entry.get_text ()
        list = string.split (tmp, " ")
        for i in list:
            if len(i):
                a = AProxy ()
                a.host = '@'
                a.ip = i
                fwdzone.a.append (a)

        return button
