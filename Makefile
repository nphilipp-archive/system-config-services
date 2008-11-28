# License: GPL v2 or later
# Copyright Red Hat Inc. 2001 - 2008

PKGNAME=system-config-services

SCM_REMOTEREPO_RE = ^ssh://(.*@)?git.fedorahosted.org/git/$(PKGNAME).git$
UPLOAD_URL = ssh://fedorahosted.org/$(PKGNAME)

SUBDIRS=po

PREFIX=/usr

BINDIR=$(PREFIX)/bin
SYSCONFDIR=/etc
SBINDIR=$(PREFIX)/sbin
DATADIR=$(PREFIX)/share
MANDIR=$(DATADIR)/man
LIBEXECDIR=$(PREFIX)/libexec

DBUS_POLICY_DIR=$(SYSCONFDIR)/dbus-1/system.d
DBUS_SERVICE_DIR=$(DATADIR)/dbus-1/system-services
POLKIT_POLICY_DIR=$(DATADIR)/PolicyKit/policy

PKGDATADIR=$(DATADIR)/$(PKGNAME)
GLADEDIR=$(PKGDATADIR)

PY_SRC_DIR		= src
PY_SRC_APPS		= gui.py system-config-services-mechanism.py
_PY_SRC_APPS	= $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_APPS))
PY_SRC_MODULES	= scservices
_PY_SRC_MODULE_FILES	= $(shell find $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_MODULES)) -type f -a -name "*.py")
PY_SOURCES		= $(_PY_SRC_APPS) $(_PY_SRC_MODULE_FILES)

all:	config $(PKGNAME).desktop py-build
	rm -f src/$(PKGNAME)
	ln -snf gui.py src/$(PKGNAME)

include rpmspec_rules.mk
include py_rules.mk
include git_rules.mk
include upload_rules.mk

src/scservices/config.py:	src/scservices/config.py.in $(PKGNAME).spec
	sed -e 's,\@DATADIR\@,$(DATADIR),g; s,\@VERSION\@,$(PKGVERSION),g;' $< > $@ || rm -f $@

config:	src/scservices/config.py

%.desktop: %.desktop.in po/$(PKGNAME).pot po/*.po
	intltool-merge -u -d po/ $< $@

install:	all py-install
	$(MAKE) -C po install
	mkdir -p $(DESTDIR)$(BINDIR)
	mkdir -p $(DESTDIR)$(SBINDIR)
	mkdir -p $(DESTDIR)$(PKGDATADIR)
	mkdir -p $(DESTDIR)$(DATADIR)/icons/hicolor/48x48/apps
	mkdir -p $(DESTDIR)$(DATADIR)/applications
	mkdir -p $(DESTDIR)$(MANDIR)/man8
	mkdir -p $(DESTDIR)$(DBUS_POLICY_DIR)
	mkdir -p $(DESTDIR)$(DBUS_SERVICE_DIR)
	mkdir -p $(DESTDIR)$(POLKIT_POLICY_DIR)

	install -m 0644 pixmaps/*.png $(DESTDIR)$(PKGDATADIR)
	install -m 0644 pixmaps/$(PKGNAME).png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	install -m 0644 man/$(PKGNAME).8 $(DESTDIR)$(MANDIR)/man8
	for file in $(_PY_SRC_APPS); do \
		install -m 0755 "$$file" "$(DESTDIR)$(PKGDATADIR)/"; \
	done
	install -m 0644 src/$(PKGNAME).glade $(DESTDIR)$(GLADEDIR)
	install -m 0644 $(PKGNAME).desktop $(DESTDIR)$(DATADIR)/applications/$(PKGNAME).desktop

	install -m 0644 config/org.fedoraproject.Config.Services.conf $(DESTDIR)$(DBUS_POLICY_DIR)/
	install -m 0644 config/org.fedoraproject.Config.Services.service $(DESTDIR)$(DBUS_SERVICE_DIR)/
	install -m 0644 config/org.fedoraproject.config.services.policy $(DESTDIR)$(POLKIT_POLICY_DIR)/

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

clean: py-clean
	@rm -fv *~
	@rm -fv src/*.pyc src/*.pyo
	@rm -fv system-config-services.desktop
