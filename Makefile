# License: GPL v2 or later
# Copyright Red Hat Inc. 2001 - 2007

PKGNAME=system-config-services

HGUPSTREAM_RE=^ssh://[^@]+@hg.fedorahosted.org//hg/$(PKGNAME)$$
HGREPO=$(shell hg showconfig | awk -F= '/paths.default=/ { print $$2 }')
PKGVERSION=$(shell awk '/Version:/ { print $$2 }' $(PKGNAME).spec)
HGTAG=$(PKGNAME)-$(subst .,_,$(PKGVERSION))

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

MAKEFILE        := $(lastword $(MAKEFILE_LIST))
TOPDIR          := $(abspath $(dir $(abspath $(MAKEFILE))))
DOC_MODULE      = $(PKGNAME)
DOC_ABS_SRCDIR  = $(TOPDIR)/doc
DOC_FIGURES_DIR = images
DOC_FIGURES     = system-config-services.png
DOC_ENTITIES    = distro-specifics.ent system-config-services-distro-specifics.ent system-config-services-abstract.xml system-config-services-content.xml
DOC_LINGUAS     = af sq am ar hy as az bal eu eu_ES be be@latin bn bn_IN bs pt_BR en_GB bg my ca zh_CN zh_TW hr cs da nl dz et fi fr gl ka de el gu he hi hu is ilo id it ja kn ko ku lo lv lt mk mai ms ml mr mn ne nso no nb nn or fa pl pt pa ro ru sr si sk sl es sv tl ta te th tr uk ur vi cy zu

PY_SRC_DIR		= src
PY_SRC_APPS		= gui.py system-config-services-mechanism.py
_PY_SRC_APPS	= $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_APPS))
PY_SRC_MODULES	= scservices
_PY_SRC_MODULE_FILES	= $(shell find $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_MODULES)) -type f -a -name "*.py")
PY_SOURCES		= $(_PY_SRC_APPS) $(_PY_SRC_MODULE_FILES)

all:	config $(PKGNAME).desktop $(PKGNAME).console py-build doc-all
	rm -f src/$(PKGNAME)
	ln -snf gui.py src/$(PKGNAME)

include py_rules.mk
include doc_rules.mk
include console_rules.mk

src/scservices/config.py:	src/scservices/config.py.in $(PKGNAME).spec
	sed -e 's,\@DATADIR\@,$(DATADIR),g; s,\@VERSION\@,$(PKGVERSION),g;' $< > $@ || rm -f $@

config:	src/scservices/config.py

%.desktop: %.desktop.in po/$(PKGNAME).pot po/*.po
	intltool-merge -u -d po/ $< $@

install:	all py-install doc-install
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

checkmods:
	@if [ -n "$$(hg diff -a)" ]; then \
		echo There are modifications not yet committed. Commit these first. >&2; \
		exit 1; \
	fi

checkrepo:
ifndef BYPASSUPSTREAM
	@if [ -z "$$(echo $(HGREPO) | egrep '$(HGUPSTREAM_RE)')" ]; then \
		echo The repository $(HGREPO) is not the upstream of $(PKGNAME). >&2; \
		echo Pushing to anywhere else may not be helpful when creating an archive. >&2; \
		echo Use BYPASSUPSTREAM=1 to not access upstream or FORCEPUSH=1 to push anyway. >&2; \
		exit 1; \
	fi
endif

incoming: checkrepo
	@if [ -n "$$(hg incoming --quiet --bundle $(HGREPO))" ]; then \
		echo There are incoming changes which need to be integrated. >&2; \
		echo Pull them with "hg pull; hg update" and resolve possible conflicts. >&2; \
		exit 1; \
	fi

tag:
ifndef FORCETAG
	@if hg diff -r "$(HGTAG)" >& /dev/null; then \
		echo "Tag $(HGTAG) exists already. Use FORCETAG=1 to force tagging." >&2 ; \
		exit 1; \
	fi
endif
	@if [ -n "$(FORCETAG)" ]; then \
		FORCE=-f; \
	else \
		FORCE=""; \
	fi; \
	LASTTAG="$$(hg tags -q | head -n 2 | tail -n 1)"; \
	if [ -n "$$LASTTAG" -a -z "$$(hg diff --exclude .hgtags -r $$LASTTAG)" ]; then \
		echo "No differences to last tagged release '$$LASTTAG'. Not tagging."; \
	else \
		echo "Tagging '$(HGTAG)'."; \
		hg tag $$FORCE $(HGTAG); \
	fi

ifdef FORCEPUSH
archivepush:
else
archivepush: checkrepo
endif
ifndef BYPASSUPSTREAM
	@echo Pushing to repository $(HGREPO).
	@if ! hg push $(HGREPO); then \
		echo Pushing failed. >&2; \
		echo Use NOPUSH=1 to bypass pushing. >&2; \
		exit 1; \
	fi
endif

archive: checkmods incoming tag archivepush
ifndef FORCEARCHIVE
	@if [ -e "${PKGNAME}-$(PKGVERSION).tar.bz2" ]; then \
		echo "File ${PKGNAME}-$(PKGVERSION).tar.bz2 exists already." >&2; \
		echo "Use FORCEARCHIVE=1 to force overwriting it." >&2; \
		exit 1; \
	fi
endif
	@hg archive -r$(HGTAG) -t tbz2 "${PKGNAME}-$(PKGVERSION).tar.bz2"
	@echo "The archive is in ${PKGNAME}-$(PKGVERSION).tar.bz2"

snapsrc: archive
	@rpmbuild -ta $(PKGNAME)-$(PKGVERSION).tar.bz2

local:
	@hg archive -t tbz2 "${PKGNAME}-$(PKGVERSION).tar.bz2"
	@echo "The _local_ archive is in ${PKGNAME}-$(PKGVERSION).tar.bz2"

clean: doc-clean console-clean
	@rm -fv *~
	@rm -fv src/*.pyc src/*.pyo
	@rm -fv system-config-services.desktop

dif:	diff

diff:
	@echo Differences to tag $(HGTAG):
	@echo
	@hg diff -r$(HGTAG) -X .hgtags

sdif:	shortdiff

shortdiff:
	@echo Files changed since tag $(HGTAG):
	@hg diff -r$(HGTAG) -X .hgtags | egrep '^---|^\+\+\+' | sed 's:^...[   ][      ]*[ab]/::g' | sort -u

llog:	lastlog

lastlog:
	@echo Log since tag $(HGTAG):
	@hg log -v -r $(HGTAG):
