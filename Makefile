# License: GPL v2 or later
# Copyright Red Hat Inc. 2001 - 2009, 2013

PKGNAME=system-config-services

SCM_REMOTEREPO_RE = ^ssh://(.*@)?git.fedorahosted.org/git/$(PKGNAME).git$
UPLOAD_URL = ssh://fedorahosted.org/$(PKGNAME)

PREFIX=/usr

BINDIR=$(PREFIX)/bin
SYSCONFDIR=/etc
SBINDIR=$(PREFIX)/sbin
DATADIR=$(PREFIX)/share
MANDIR=$(DATADIR)/man
LIBEXECDIR=$(PREFIX)/libexec

DBUS_POLICY_DIR=$(SYSCONFDIR)/dbus-1/system.d
DBUS_SERVICE_DIR=$(DATADIR)/dbus-1/system-services

POLKIT_FILES=config/org.fedoraproject.config.services.policy.0 \
			 config/org.fedoraproject.config.services.policy.1

PKGDATADIR=$(DATADIR)/$(PKGNAME)
GLADEDIR=$(PKGDATADIR)

PY_SRC_DIR		= src
PY_SRC_APPS		= gui.py system-config-services-mechanism.py
_PY_SRC_APPS	= $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_APPS))
PY_SRC_MODULES	= scservices
_PY_SRC_MODULE_FILES	= $(shell find $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_MODULES)) -type f -a -name "*.py")
PY_SOURCES		= $(_PY_SRC_APPS) $(_PY_SRC_MODULE_FILES)

GLADE_SOURCES	= $(wildcard src/*.glade)

PO_SOURCES		= $(PY_SOURCES) $(PO_GLADEH_FILES) $(DESKTOPINH_FILES) $(POLKITINH_FILES)

all:	config py-build po-all polkit-all desktop-all
	rm -f src/$(PKGNAME)
	ln -snf gui.py src/$(PKGNAME)

include rpmspec_rules.mk
include py_rules.mk
include git_rules.mk
include upload_rules.mk
include polkit_rules.mk
include desktop_rules.mk
include po_rules.mk

src/scservices/config.py:	src/scservices/config.py.in $(PKGNAME).spec .scminfo
	sed -e 's,\@DATADIR\@,$(DATADIR),g; s,\@VERSION\@,$(PKGVERSION),g;s,\@COPYRIGHT_ENDS\@,$(SCM_LAST_CHANGE_YEAR),g' $< > $@ || rm -f $@

config:	src/scservices/config.py

install:	all py-install po-install polkit-install desktop-install
	install -d $(DESTDIR)$(PKGDATADIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(SBINDIR)

	install -m 0644 pixmaps/*.png $(DESTDIR)$(PKGDATADIR)
	install -D -m 0644 pixmaps/$(PKGNAME).png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/$(PKGNAME).png
	install -D -m 0644 man/$(PKGNAME).8 $(DESTDIR)$(MANDIR)/man8/$(PKGNAME).8
	for file in $(_PY_SRC_APPS); do \
		install -m 0755 "$$file" "$(DESTDIR)$(PKGDATADIR)/"; \
	done
	install -D -m 0644 src/$(PKGNAME).glade $(DESTDIR)$(GLADEDIR)/$(PKGNAME).glade

	install -D -m 0644 config/org.fedoraproject.Config.Services.conf $(DESTDIR)$(DBUS_POLICY_DIR)/org.fedoraproject.Config.Services.conf
	install -D -m 0644 config/org.fedoraproject.Config.Services.service $(DESTDIR)$(DBUS_SERVICE_DIR)/org.fedoraproject.Config.Services.service

	python -c 'import compileall; compileall.compile_dir ("'"$(DESTDIR)$(PKGDATADIR)"'", ddir="'"$(PKGDATADIR)"'", maxlevels=10, force=1)'
	softdir=$(PKGDATADIR); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(PREFIX) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/gui.py $(DESTDIR)$(BINDIR)/system-config-services; \
	ln  -fs ../$${softdir}/gui.py $(DESTDIR)$(BINDIR)/serviceconf; \
	ln  -fs ../$${softdir}/gui.py $(DESTDIR)$(SBINDIR)/system-config-services; \
	ln  -fs ../$${softdir}/gui.py $(DESTDIR)$(SBINDIR)/serviceconf;

clean: py-clean po-clean polkit-clean desktop-clean
	@rm -fv src/scservices/config.py
