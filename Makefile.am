AUTOMAKE_OPTIONS = foreign 1.4

SUBDIRS = src po man

EXTRA_DIST = \
	redhat-config-services.spec		\
	redhat-config-services.desktop.in 	\
	redhat-config-services.desktop	 	\
	redhat-config-services.console		\
	redhat-config-services.pam		\
	pycheckrc				\
	pixmaps/redhat-config-services.png	\
	intltool-extract.in			\
	intltool-merge.in			\
	intltool-update.in			\
	ChangeLog

CLEANFILES=$(applications_DATA)
DISTCLEANFILES=intltool-extract intltool-merge intltool-update
MAINTAINERCLEANFILES=ChangeLog

@INTLTOOL_DESKTOP_RULE@

.PHONY: changelog srpm

applicationsdir=$(datadir)/applications
applications_DATA=redhat-config-services.desktop
applications_in_files=$(applications_DATA:.desktop=.desktop.in)

install-data-hook:
	$(mkinstalldirs) $(DESTDIR)$(datadir)/pixmaps
	$(mkinstalldirs) $(DESTDIR)$(sysconfdir)/security/console.apps
	$(mkinstalldirs) $(DESTDIR)$(sysconfdir)/pam.d
	$(mkinstalldirs) $(DESTDIR)$(prefix)/bin/
	$(INSTALL_DATA) $(srcdir)/redhat-config-services.console $(DESTDIR)$(sysconfdir)/security/console.apps/redhat-config-services
	$(INSTALL_DATA) $(srcdir)/redhat-config-services.pam $(DESTDIR)$(sysconfdir)/pam.d/redhat-config-services
	$(INSTALL_DATA) $(srcdir)/pixmaps/redhat-config-services.png $(DESTDIR)$(datadir)/pixmaps
	ln -fs consolehelper $(DESTDIR)$(prefix)/bin/redhat-config-services
	ln -fs consolehelper $(DESTDIR)$(prefix)/bin/serviceconf
	ln -fs redhat-config-services $(DESTDIR)$(sysconfdir)/security/console.apps/serviceconf
	ln -fs redhat-config-services $(DESTDIR)$(sysconfdir)/pam.d/serviceconf

uninstall-local:
	rm -f $(DESTDIR)$(sysconfdir)/pam.d/redhat-config-services
	rm -f $(DESTDIR)$(prefix)/bin/redhat-config-services
	rm -f $(DESTDIR)$(datadir)/pixmaps/redhat-config-services.png
	ln -f $(DESTDIR)$(prefix)/bin/serviceconf

changelog:
	rcs2log | sed -e 's|/usr/local/CVS/redhat-config-network/||g' \
		-e 's|@.*\.redhat\.com|@redhat.com|g' > ChangeLog

clean:
	rm -f redhat-config-services.desktop
	rm -f *~

PKGNAME=${PACKAGE}
VERSION=@VERSION@
CVSTAG=r$(subst .,-,$(VERSION))

archive: distcheck changelog
	cvs ci -m "release $(VERSION)"
	cvs tag -cFR $(CVSTAG) .
	@rm -rf /tmp/${PKGNAME}-$(VERSION) /tmp/${PKGNAME}
	@CVSROOT=`cat CVS/Root`; cd /tmp; cvs -d $$CVSROOT export -r$(CVSTAG) ${PKGNAME}
	@cd /tmp/${PKGNAME};./autogen.sh
	@mv /tmp/${PKGNAME} /tmp/${PKGNAME}-$(VERSION)
	@dir=$$PWD; cd /tmp; tar cvzf $$dir/${PKGNAME}-$(VERSION).tar.gz ${PKGNAME}-$(VERSION)
	@rm -rf /tmp/${PKGNAME}-$(VERSION)
	@echo "The archive is in ${PKGNAME}-$(VERSION).tar.gz"

srpm: archive
	rpmbuild --define "_sourcedir `pwd`" --define "_srcrpmdir `pwd`" --define "_specdir `pwd`" -ts @PACKAGE@-@VERSION@.tar.gz


