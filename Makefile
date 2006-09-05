# License: GPL
# Copyright Red Hat Inc. 2001, 2006

PKGNAME=system-config-services
VERSION=$(shell awk '/Version:/ { print $$2 }' $(PKGNAME).spec)
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(PKGNAME).spec)
CVSTAG=r$(subst .,-,$(VERSION))
SUBDIRS=po

PREFIX=/usr

BINDIR=$(PREFIX)/bin
SBINDIR=$(PREFIX)/sbin
MANDIR=/usr/share/man
DATADIR=$(PREFIX)/share

PKGDATADIR=$(DATADIR)/$(PKGNAME)
GLADEDIR=$(PKGDATADIR)

PAMD_DIR        = /etc/pam.d
SECURITY_DIR    = /etc/security/console.apps

all:	$(PKGNAME).desktop
	rm -f src/$(PKGNAME)
	ln -snf serviceconf.py src/$(PKGNAME)

po/$(PKGNAME).pot:: all

#%.desktop.in.h:	%.desktop.in
#	intltool-extract --type=gettext/ini $<

%.desktop: %.desktop.in po/$(PKGNAME).pot po/*.po
	intltool-merge -u -d po/ $< $@

install:	all
	mkdir -p $(DESTDIR)$(SECURITY_DIR)
	mkdir -p $(DESTDIR)$(PAMD_DIR)
	mkdir -p $(DESTDIR)$(BINDIR)
	mkdir -p $(DESTDIR)$(SBINDIR)
	mkdir -p $(DESTDIR)$(PKGDATADIR)
	mkdir -p $(DESTDIR)$(DATADIR)/icons/hicolor/48x48/apps
	mkdir -p $(DESTDIR)$(DATADIR)/applications
	mkdir -p $(DESTDIR)$(MANDIR)/man8

	install $(PKGNAME).console $(DESTDIR)$(SECURITY_DIR)/$(PKGNAME)
	install $(PKGNAME).pam $(DESTDIR)$(PAMD_DIR)/$(PKGNAME)
	install pixmaps/*.png $(DESTDIR)$(PKGDATADIR)
	install pixmaps/$(PKGNAME).png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	install man/$(PKGNAME).8 $(DESTDIR)$(MANDIR)/man8
	sed -e 's/\@VERSION\@/$(VERSION)/g' src/serviceconf.py > $(DESTDIR)$(PKGDATADIR)/serviceconf.py
	chmod 755 $(DESTDIR)$(PKGDATADIR)/serviceconf.py
	install -m 0755 src/checklist.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0755 src/nonblockingreader.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0755 src/servicemethods.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0644 src/serviceconf.glade $(DESTDIR)$(GLADEDIR)
	install -m 0644 $(PKGNAME).desktop $(DESTDIR)$(DATADIR)/applications/$(PKGNAME).desktop

	ln -sf consolehelper $(DESTDIR)$(BINDIR)/$(PKGNAME)
	ln -sf consolehelper $(DESTDIR)$(BINDIR)/serviceconf
	ln -sf $(PKGNAME) $(DESTDIR)$(SECURITYDIR)/serviceconf
	ln -sf $(PKGNAME) $(DESTDIR)$(PAMD_DIR)/serviceconf

	python -c 'import compileall; compileall.compile_dir ("'"$(DESTDIR)$(PKGDATADIR)"'", ddir="'"$(PKGDATADIR)"'", maxlevels=10, force=1)'
	softdir=$(PKGDATADIR); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(prefix) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/system-config-services; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/serviceconf;

archive: changelog_cvs
	cvs tag -cR $(CVSTAG) .
	@rm -rf /tmp/$(PKGNAME)-$(VERSION) /tmp/$(PKGNAME)
	@CVSROOT=`cat CVS/Root`; cd /tmp; cvs -d $$CVSROOT export -r$(CVSTAG) $(PKGNAME)
	@mv /tmp/$(PKGNAME) /tmp/$(PKGNAME)-$(VERSION)
	@dir=$$PWD; cd /tmp; tar cvjf $$dir/$(PKGNAME)-$(VERSION).tar.bz2 $(PKGNAME)-$(VERSION)
	@rm -rf /tmp/$(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.bz2"

snapsrc: archive
	@rpmbuild -ta $(PKGNAME)-$(VERSION)-$(RELEASE).tar.bz2

local:
	@rm -rf $(PKGNAME)-$(VERSION).tar.gz
	@rm -rf /tmp/$(PKGNAME)-$(VERSION) /tmp/$(PKGNAME)
	@mkdir /tmp/$(PKGNAME)
	@cp -a * /tmp/$(PKGNAME)
	@mv /tmp/$(PKGNAME) /tmp/$(PKGNAME)-$(VERSION)
	@dir=$$PWD; cd /tmp; tar cvjf $$dir/$(PKGNAME)-$(VERSION).tar.bz2 $(PKGNAME)-$(VERSION)
	@rm -rf /tmp/$(PKGNAME)-$(VERSION)      
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.bz2"

changelog:
	rcs2log -h redhat.com \
		| sed -e 's|/usr/local/CVS/system-config-services/||g' \
		> ChangeLog.new
	if test -f ChangeLog; then \
		cp -dpf ChangeLog ChangeLog.old; \
	else \
		touch ChangeLog.old; \
	fi
	cat ChangeLog.new ChangeLog.old > ChangeLog
	rm -f ChangeLog.new ChangeLog.old

changelog_cvs:	changelog
	cvs commit -m '' ChangeLog

pycheck:
	pychecker -F pycheckrc src/*.py

clean:
	@rm -fv *~
	@rm -fv src/*.pyc src/*.pyo
	@rm -fv system-config-services.desktop
