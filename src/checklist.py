# -*- coding: utf-8 -*-
# checklist.py: A class (derived from GtkTreeView) that provides a list of
#               checkbox / text string pairs
#
# Brent Fox <bfox@redhat.com>
# Jeremy Katz <katzj@redhat.com>
# Nils Philippsen <nphilipp@redhat.com>
#
# Copyright © 2000-2006 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gobject

class CheckList (gtk.TreeView):
    """A class (derived from gtk.TreeView) that provides a list of
    checkbox(es) / text string pairs"""

    def __init__ (self, num_checkboxes = 1):
        args = [gobject.TYPE_BOOLEAN] * num_checkboxes
        args.append (gobject.TYPE_STRING)
        self.store = gtk.ListStore (*args)

        gtk.TreeView.__init__ (self, self.store)
        
        self.num_checkboxes = num_checkboxes
        self.checkboxrenderer = []
        
        for i in range(0, num_checkboxes):
            self.checkboxrenderer.append (gtk.CellRendererToggle ())
            column = gtk.TreeViewColumn('', self.checkboxrenderer[i], active=i)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(40)
            column.set_clickable(True)
            self.checkboxrenderer[i].connect ("toggled", self.toggled_item, i)
            self.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Text', renderer, text=num_checkboxes)
        column.set_clickable(False)
        self.append_column(column)

        self.set_rules_hint(False)
        self.set_headers_visible(False)
        self.columns_autosize()
        self.set_enable_search(False)

        # keep track of the number of rows we have so we can
        # iterate over them all
        self.num_rows = 0

    def append_row (self, text, init_valueList):
        """Add a row to the list.
        text: text to display in the row
        init_value: initial state of the indicator"""
        #print "CheckList.append_row (%s, %s, %s)" % (self, text, init_valueList)

        iter = self.store.append(None)
        for i in range(0, self.num_checkboxes):
            #print "self.store.set_value(%s, %s, %s)" % (iter, i, int(init_valueList[i]))
            self.store.set_value(iter, i, int(init_valueList[i]))

        # add the text for the number of columns we have
        #print "self.store.set_value(%s, %s, %s)" % (iter, self.num_checkboxes, text)
        self.store.set_value(iter, self.num_checkboxes, text)

        self.num_rows = self.num_rows + 1


    def toggled_item(self, data, row, column):
        """Set a function to be called when the value of a row is toggled.
        The  function will be called with two arguments, the clicked item
        in the row and a string for which row was clicked."""
        
        iter = self.store.get_iter((int(row),))
        val = self.store.get_value(iter, column)
        self.store.set_value(iter, column, not val)


    def clear (self):
        "Remove all rows"
        self.store.clear()
        self.num_rows = 0


    def get_active(self, row, column):
        """Return FALSE or TRUE as to whether or not the row is toggled
        similar to GtkToggleButtons"""
        #print "CheckList.get_active (%s, %s, %s)" % (self, row, column)

        iter = self.store.get_iter((row,))
        #print "    ->", self.store.get_value(iter, column)
        return self.store.get_value(iter, column)


    def set_active(self, row, is_active):
        "Set row to be is_active, similar to GtkToggleButton"

        iter = self.store.get_iter((row,))
        self.store.set_value(iter, 0, is_active)


    def get_text(self, row, column):
        "Get the text from row and column"
        #print "CheckList.get_text (%s, %s, %s)" % (self, row, column)

        iter = self.store.get_iter(row)
        #print "    ->", self.store.get_value(iter, column)
        return self.store.get_value(iter, column)


    def set_column_title(self, column, title):
        "Set the title of column to title"

        col = self.get_column(column)
        if col:
            col.set_title(title)


    def set_column_min_width(self, column, min):
        "Set the minimum width of column to min"

        col = self.get_column(column)
        if col:
            col.set_min_width(min)


    def set_column_clickable(self, column, clickable):
        "Set the column to be clickable"

        col = self.get_column(column)
        if col:
            col.set_clickable(clickable)
            

    def set_column_sizing(self, column, sizing):
        "Set the column to use the given sizing method"

        col = self.get_column(column)
        if col:
            col.set_sizing(sizing)

    def get_column_visible (self, column):
        #print "CheckList.get_column_visible (%s, %s)" % (self, column)
        col = self.get_column(column)
        if col:
            return col.get_visible ()

    def set_column_visible(self, column, visible):
        "Set the column visibility"

        col = self.get_column(column)
        if col:
            col.set_visible(visible)

    def set_headers_visible(self, visible):
        "Set the column visibility"

        if visible != 0:
            gtk.TreeView.set_headers_visible(self, True)
        else:
            gtk.TreeView.set_headers_visible(self, False)

    def set_column_sort_id(self, column, id):
        "Set the sort id of column to id"

        col = self.get_column(column)
        if col:
            col.set_sort_column_id(id)
