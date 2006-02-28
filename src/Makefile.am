PYTHON_FILES = checklist.py nonblockingreader.py serviceconf.py servicemethods.py servicecontrol.py

GLADE_FILES = serviceconf.glade

EXTRA_DIST = $(PYTHON_FILES) $(GLADE_FILES)

execdir = $(sbindir)

all-local: 
	rm -f system-config-services
	ln -s serviceconf.py system-config-services

gladedir = $(pkgdatadir)
glade_DATA = $(GLADE_FILES)

install-exec-local:
	mkdir -p $(DESTDIR)$(sbindir) $(DESTDIR)$(bindir) $(DESTDIR)$(pkgdatadir)
	sed -e 's/\@VERSION\@/@VERSION@/g' $(srcdir)/serviceconf.py > $(DESTDIR)$(pkgdatadir)/serviceconf.py
	chmod 755 $(DESTDIR)$(pkgdatadir)/serviceconf.py
	install -m 0755 $(srcdir)/checklist.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/nonblockingreader.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/servicemethods.py $(DESTDIR)$(pkgdatadir)/
	install -m 0755 $(srcdir)/servicecontrol.py $(DESTDIR)$(pkgdatadir)/
	python -c 'import compileall; compileall.compile_dir ("'"$(DESTDIR)$(pkgdatadir)"'", ddir="'"$(pkgdatadir)"'", maxlevels=10, force=1)'
	softdir=$(pkgdatadir); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(prefix) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/system-config-services; \
	ln  -fs ../$${softdir}/serviceconf.py $(DESTDIR)$(sbindir)/serviceconf;

uninstall-local:
	rm -fr $(DESTDIR)$(pkgdatadir)
	rm -f  $(DESTDIR)$(sbindir)/system-config-services
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
