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

# commands
DIFF		= /usr/bin/diff
GREP		= /bin/grep

# PO catalog handling
MSGMERGE	= msgmerge -v -N
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

po_diff_and_mv_or_rm  = \
	if [ ! -f "$(1)" ] || ($(DIFF) "$(1)" "$(2)" | $(GREP) -v '^. "POT-Creation-Date:' | $(GREP) -q '^[<>] .'); then \
		echo "Creating/updating $(1)"; \
		mv -f $(2) $(1); \
	else \
		rm -f $(2); \
	fi

po_diff_and_mv_or_rm_func = \
	function po_diff_and_mv_or_rm () { \
		$(call po_diff_and_mv_or_rm,$$1,$$2) \
	}

$(POTFILE): $(SRCFILES)
	$(XGETTEXT) --keyword=_ --keyword=N_ $(SRCFILES)
	@$(call diff_and_mv_or_rm,$(POTFILE),$(NLSPACKAGE).po)

update-po: Makefile $(POTFILE) refresh-po

refresh-po: Makefile
	@$(po_diff_and_mv_or_rm_func); \
	for cat in $(POFILES); do \
		lang=`basename $$cat .po`; \
		if $(MSGMERGE) $$lang.po $(POTFILE) > $$lang.pot ; then \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
			po_diff_and_mv_or_rm $$lang.pot $$lang.po; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi; \
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


