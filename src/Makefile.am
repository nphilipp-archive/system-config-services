PYTHON_FILES = checklist.py dnsdata.py serviceconf.py dnsdata_base.py  FwdZone.py  servicemethods.py

GLADE_FILES = serviceconf.glade

EXTRA_DIST = $(PYTHON_FILES) $(GLADE_FILES) 

execdir = $(sbindir)

all-local: 
	rm -f redhat-config-services
	ln -s serviceconf.py redhat-config-services

gladedir = $(pkgdatadir)
glade_DATA = $(GLADE_FILES)

install-exec-local:
	mkdir -p $(DESTDIR)$(sbindir) $(DESTDIR)$(bindir) $(DESTDIR)$(pkgdatadir)
	install -m 0755 $(srcdir)/serviceconf.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/checklist.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/dnsdata.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/dnsdata_base.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/FwdZone.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/servicemethods.py $(DESTDIR)$(pkgdatadir)/
	softdir=$(pkgdatadir); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(prefix) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/redhat-config-services; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/serviceconf;

uninstall-local:
	rm -fr $(DESTDIR)$(pkgdatadir)
	rm -f  $(DESTDIR)$(sbindir)/redhat-config-services
	rm -f  $(DESTDIR)$(sbindir)/serviceconf

docs:
	cd $(srcdir)
	python @PYDOC@ -w $(PYTHON_FILES)
	mv *.html doc

pycheck:
	pychecker -F $(top_srcdir)/pycheckrc $(PYTHON_FILES)

clean:
	rm -f *.pyo *.pyc
	rm -f ${BUILT_SOURCES}
