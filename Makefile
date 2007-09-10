# License: GPL
# Copyright Red Hat Inc. 2001 - 2007

PKGNAME=system-config-services

HGUPSTREAM_RE=^ssh://[^@]+@hg.fedoraproject.org//hg/hosted/$(PKGNAME)$$
HGREPO=$(shell hg showconfig | awk -F= '/paths.default=/ { print $$2 }')
VERSION=$(shell awk '/Version:/ { print $$2 }' $(PKGNAME).spec)
HGTAG=$(PKGNAME)-$(subst .,_,$(VERSION))

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

%.desktop: %.desktop.in po/$(PKGNAME).pot po/*.po
	intltool-merge -u -d po/ $< $@

install:	all
	$(MAKE) -C po install
	mkdir -p $(DESTDIR)$(SECURITY_DIR)
	mkdir -p $(DESTDIR)$(PAMD_DIR)
	mkdir -p $(DESTDIR)$(BINDIR)
	mkdir -p $(DESTDIR)$(SBINDIR)
	mkdir -p $(DESTDIR)$(PKGDATADIR)
	mkdir -p $(DESTDIR)$(DATADIR)/icons/hicolor/48x48/apps
	mkdir -p $(DESTDIR)$(DATADIR)/applications
	mkdir -p $(DESTDIR)$(MANDIR)/man8

	install -m 0644 $(PKGNAME).console $(DESTDIR)$(SECURITY_DIR)/$(PKGNAME)
	install -m 0644 $(PKGNAME).pam $(DESTDIR)$(PAMD_DIR)/$(PKGNAME)
	install -m 0644 pixmaps/*.png $(DESTDIR)$(PKGDATADIR)
	install -m 0644 pixmaps/$(PKGNAME).png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	install -m 0644 man/$(PKGNAME).8 $(DESTDIR)$(MANDIR)/man8
	sed -e 's/\@VERSION\@/$(VERSION)/g' src/serviceconf.py > $(DESTDIR)$(PKGDATADIR)/serviceconf.py
	chmod 755 $(DESTDIR)$(PKGDATADIR)/serviceconf.py
	install -m 0755 src/checklist.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0755 src/nonblockingreader.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0755 src/servicemethods.py $(DESTDIR)$(PKGDATADIR)/
	install -m 0644 src/serviceconf.glade $(DESTDIR)$(GLADEDIR)
	install -m 0644 $(PKGNAME).desktop $(DESTDIR)$(DATADIR)/applications/$(PKGNAME).desktop

	ln -sf consolehelper $(DESTDIR)$(BINDIR)/$(PKGNAME)
	ln -sf consolehelper $(DESTDIR)$(BINDIR)/serviceconf
	ln -sf $(PKGNAME) $(DESTDIR)$(SECURITY_DIR)/serviceconf
	ln -sf $(PKGNAME) $(DESTDIR)$(PAMD_DIR)/serviceconf

	python -c 'import compileall; compileall.compile_dir ("'"$(DESTDIR)$(PKGDATADIR)"'", ddir="'"$(PKGDATADIR)"'", maxlevels=10, force=1)'
	softdir=$(PKGDATADIR); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(PREFIX) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(SBINDIR)/system-config-services; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(SBINDIR)/serviceconf;

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
	@if [ -e "${PKGNAME}-$(VERSION).tar.bz2" ]; then \
		echo "File ${PKGNAME}-$(VERSION).tar.bz2 exists already." >&2; \
		echo "Use FORCEARCHIVE=1 to force overwriting it." >&2; \
		exit 1; \
	fi
endif
	@hg archive -r$(HGTAG) -t tbz2 "${PKGNAME}-$(VERSION).tar.bz2"
	@echo "The archive is in ${PKGNAME}-$(VERSION).tar.bz2"

snapsrc: archive
	@rpmbuild -ta $(PKGNAME)-$(VERSION).tar.bz2

local:
	@hg archive -t tbz2 "${PKGNAME}-$(VERSION).tar.bz2"
	@echo "The _local_ archive is in ${PKGNAME}-$(VERSION).tar.bz2"

pycheck:
	pychecker -F pycheckrc src/*.py

clean:
	@rm -fv *~
	@rm -fv src/*.pyc src/*.pyo
	@rm -fv system-config-services.desktop
