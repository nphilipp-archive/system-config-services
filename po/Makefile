#
# Makefile for the PO files (translation) catalog
#
# $Id: Makefile,v 1.2 2006/10/20 09:56:53 nphilipp Exp $

TOP	 = ../..

# What is this package?
NLSPACKAGE	= system-config-services
POTFILE		= $(NLSPACKAGE).pot
INSTALL		= /usr/bin/install -c
INSTALL_DATA	= $(INSTALL) -m 644
INSTALL_DIR	= /usr/bin/install -d

# destination directory
INSTALL_NLS_DIR = $(DESTDIR)/usr/share/locale

# PO catalog handling
MSGMERGE	= msgmerge -v
XGETTEXT	= xgettext --default-domain=$(NLSPACKAGE) \
		  --add-comments		  
MSGFMT		= msgfmt --statistics --verbose
INTLTOOLEXTRACT	= intltool-extract

# What do we need to do
POFILES		= $(wildcard *.po)
MOFILES		= $(patsubst %.po,%.mo,$(POFILES))
PYSRC		= $(wildcard ../src/*.py)
GLADEFILES	= $(wildcard ../src/*.glade)
GLADEHFILES	= $(patsubst %.glade,%.glade.h,$(GLADEFILES))
DESKTOPINFILES	= $(wildcard ../*.desktop.in)
DESKTOPINHFILES	= $(patsubst %.desktop.in,%.desktop.in.h,$(DESKTOPINFILES))
SRCFILES	= $(PYSRC) $(GLADEHFILES) $(DESKTOPINHFILES)

all::  update-po $(MOFILES)

%.glade.h:	%.glade
	$(INTLTOOLEXTRACT) -t gettext/glade $<

%.desktop.in.h:	%.desktop.in
	$(INTLTOOLEXTRACT) -t gettext/ini $<

$(POTFILE): $(SRCFILES)
	$(XGETTEXT) --keyword=_ --keyword=N_ $(SRCFILES)
	@if cmp -s $(NLSPACKAGE).po $(POTFILE); then \
	    rm -f $(NLSPACKAGE).po; \
	else \
	    mv -f $(NLSPACKAGE).po $(POTFILE); \
	fi; \

update-po: Makefile $(POTFILE) refresh-po

refresh-po: Makefile
	for cat in $(POFILES); do \
		lang=`basename $$cat .po`; \
		if $(MSGMERGE) $$lang.po $(POTFILE) > $$lang.pot ; then \
			mv -f $$lang.pot $$lang.po ; \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi \
	done

clean:
	@rm -fv *mo *~ .depend $(GLADEHFILES) $(DESKTOPINHFILES)

install: $(MOFILES)
	@for n in $(MOFILES); do \
	    l=`basename $$n .mo`; \
	    $(INSTALL_DIR) $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES; \
	    $(INSTALL_DATA) --verbose $$n $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	done

%.mo: %.po
	$(MSGFMT) -o $@ $<

.PHONY: missing depend


