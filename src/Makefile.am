PYTHON_FILES = checklist.py serviceconf.py servicemethods.py

GLADE_FILES = serviceconf.glade

SCRIPT_FILES = redhat-config-services.sh

EXTRA_DIST = $(PYTHON_FILES) $(GLADE_FILES) $(SCRIPT_FILES)

execdir = $(sbindir)

all-local: 
	rm -f redhat-config-services
	ln -s serviceconf.py redhat-config-services

gladedir = $(pkgdatadir)
glade_DATA = $(GLADE_FILES)

install-exec-local:
	mkdir -p $(DESTDIR)$(sbindir) $(DESTDIR)$(bindir) $(DESTDIR)$(pkgdatadir)
	sed -e 's/\@VERSION\@/@VERSION@/g' $(srcdir)/serviceconf.py > $(DESTDIR)$(pkgdatadir)/serviceconf.py
	chmod 755 $(DESTDIR)$(pkgdatadir)/serviceconf.py
	install -m 0755 $(srcdir)/checklist.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/servicemethods.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/redhat-config-services.sh $(DESTDIR)$(pkgdatadir)/redhat-config-services
	softdir=$(pkgdatadir); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(prefix) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/redhat-config-services $(DESTDIR)$(sbindir)/redhat-config-services; \
	ln  -fs ../$${softdir}/redhat-config-services $(DESTDIR)$(sbindir)/serviceconf;

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
