# -*- RPM-SPEC -*-
Summary: system-config-services is an initscript and xinetd configuration utility
Name: system-config-services
Version: 0.9.10
Release: 1%{?dist}
URL: http://fedoraproject.org/wiki/SystemConfig/services
# We are upstream, thus the source is only available from within this source
# package.
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires: /sbin/chkconfig
Requires: pygtk2, pygtk2-libglade, rhpl
Requires: usermode >= 1.36, usermode-gtk
Requires: htmlview
Requires: python >= 2.3.0
Requires(post): hicolor-icon-theme
Requires(post): gtk2
Requires(postun): hicolor-icon-theme
Requires(postun): gtk2
BuildRequires: intltool sed desktop-file-utils
BuildRequires: perl(XML::Parser)
BuildRequires: gettext
Obsoletes: serviceconf
Obsoletes: redhat-config-services

%description
system-config-services is a utility which allows you to configure which services
should be enabled on your machine.

%prep
%setup -q

%build
make

%install
rm -rf %{buildroot}
make DESTDIR=%buildroot install

desktop-file-install --vendor system --delete-original      \
  --dir %{buildroot}%{_datadir}/applications                \
  --add-category X-Red-Hat-Base                             \
  %{buildroot}%{_datadir}/applications/%{name}.desktop

%find_lang %name

%post
touch --no-create %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  gtk-update-icon-cache -q %{_datadir}/icons/hicolor
fi

%postun
touch --no-create %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  gtk-update-icon-cache -q %{_datadir}/icons/hicolor
fi

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root)
%doc COPYING
%doc docs/*
%{_sbindir}/*
%{_bindir}/*
%{_datadir}/applications/system-config-services.desktop
%{_datadir}/icons/hicolor/48x48/apps/system-config-services.png
%{_datadir}/system-config-services
%config %{_sysconfdir}/pam.d/system-config-services
%config %{_sysconfdir}/security/console.apps/system-config-services
%config %{_sysconfdir}/security/console.apps/serviceconf
%config %{_sysconfdir}/pam.d/serviceconf
%{_mandir}/*/system-config-services.8*

%changelog
* Mon Sep 10 2007 Nils Philippsen <nphilipp@redhat.com>
- make use of force tagging (since mercurial 0.9.4)

* Mon Jul 23 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.10
- make "make archive" work with Hg
- disable automatic ChangeLog generation

* Wed Jun 27 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.9
- fix desktop file category (#245891)

* Fri May 04 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.8
- pick up updated translations (#223447)

* Wed Apr 25 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.7
- pick up updated translations
- work around issues with UTF-8 in translatable strings (#232809)

* Thu Mar 22 2007 Nils Philippsen <nphilipp@redhat.com>
- update URL

* Tue Mar 20 2007 Nils Philippsen <nphilipp@redhat.com>
- mention that we are upstream
- use preferred buildroot
- fix licensing blurb in PO files
- recode spec file to UTF-8

* Wed Jan 31 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.6
- fix up service metadata reading a bit (#217591)

* Wed Jan 31 2007 Nils Philippsen <nphilipp@redhat.com> - 0.9.5
- use "install -m" to install a lot of files without executable bits (#222579)

* Wed Dec  6 2006 Harald Hoyer <harald@redhat.com> - 0.9.4
- fixed service start/stop (#218429)
- translation update (#216558)
- Resolves: rhbz#216558, rhbz#218429

* Fri Nov 24 2006 Nils Philippsen <nphilipp@redhat.com> - 0.9.3
- pick up updated translations (#216558)

* Fri Oct 20 2006 Nils Philippsen <nphilipp@redhat.com> - 0.9.2
- use intltool-extract for i18n of glade files (#211248) and desktop file
  (#207345)

* Tue Sep 05 2006 Nils Philippsen <nphilipp@redhat.com> - 0.9.1
- don't disable Start/Stop/Restart upon reverting changes (#202722)
- add dist tag
- install po files (again)
- require gettext for building
- fix tagging for make archive
- fix circular make dependency
- remove duplicate message definitions

* Fri Aug 18 2006 Nils Philippsen <nphilipp@redhat.com>
- make revert work again (#202467)
- don't show all runlevels when starting

* Mon Jun 05 2006 Jesse Keating <jkeating@redhat.com> - 0.9.0-2
- Added BuildRequires perl-XML-Parser (#194179)
- Added Requires(post) and (postun) gtk2

* Fri May 19 2006 Nils Philippsen <nphilipp@redhat.com>
- rip out autofoo
- use bzip2'ed tarballs

* Fri Mar 03 2006 Nils Philippsen <nphilipp@redhat.com> - 0.9.0
- require hicolor-icon-theme (#182878, #182879)

* Wed Feb 28 2006 Florian Festi <ffesti@redhat.com> 
- rewrote large parts of servicemethods (OO design, better handling of old/new
  settings, read headers of init scripts completely)
- first implementation of widgets to control services (intended for tools
  configuring single services like nfs, samba, bind, ...), still missing: i18n,
  dependencies on other services (like portmap)

* Fri Jan 27 2006 Nils Philippsen <nphilipp@redhat.com> - 0.8.99.2
- fix saving xinetd services

* Fri Jan 27 2006 Nils Philippsen <nphilipp@redhat.com> - 0.8.99.1
- implement daemons and xinetd services on separate tabs

* Mon Jan 09 2006 Nils Philippsen <nphilipp@redhat.com>
- separate daemons and xinetd based services
- enable Serbian translation files

* Fri Oct 14 2005 Nils Philippsen <nphilipp@redhat.com>
- don't use pam_stack (#170645)

* Tue Aug 16 2005 Nils Philippsen <nphilipp@redhat.com> - 0.8.26
- revamp getting output from external commands (#162884)
- package %{_bindir}/serviceconf symlink (#165099)

* Mon May 09 2005 Nils Philippsen <nphilipp@redhat.com> - 0.8.25
- pick up updated translations

* Fri May 06 2005 Nils Philippsen <nphilipp@redhat.com> - 0.8.24
- make "make update-po" pick up translatable strings in desktop file (#156801)

* Fri May 06 2005 Nils Philippsen <nphilipp@redhat.com> - 0.8.23
- pick up new translations

* Wed Apr 27 2005 Jeremy Katz <katzj@redhat.com> - 0.8.22-2
- silence %%post

* Fri Apr 01 2005 Nils Philippsen <nphilipp@redhat.com> 0.8.22-1
- fix deprecation warnings (#153052) with patch by Colin Charles
- update the GTK+ theme icon cache on (un)install (Christopher Aillon)

* Thu Mar 24 2005 Nils Philippsen <nphilipp@redhat.com> 0.8.21-1
- connect toggled signals of service/runlevel checkboxes to enable saving again
  (#151982)
- consolidate on_optRL*_toggled
- connect delete_event of mainWindow to ask whether things should be saved
  before quitting
- tab -> space indentation to avoid ambiguity
- change some typos

* Fri Mar 18 2005 Nils Philippsen <nphilipp@redhat.com> 0.8.20-1
- don't read from /dev/null when restarting xinetd/services to prevent hangs
- build toolbar in glade to avoid DeprecationWarnings (#134978)
- dynamic, translated column titles for runlevel columns

* Thu Feb 17 2005 Daniel J Walsh <dwalsh@redhat.com> 0.8.19-1
- Added patch from Charlie Brej 

* Fri Jan 28 2005 Nils Philippsen <nphilipp@redhat.com> 0.8.18-1
- fix off-by-one which prevented saving changes to the last service in the list
  (#139456)

* Tue Jan 04 2005 Nils Philippsen <nphilipp@redhat.com> 0.8.17-1
- throw away stderr to not be confused by error messages (#142983)

* Wed Dec 08 2004 Nils Philippsen <nphilipp@redhat.com> 0.8.16-1
- don't hardcode python 2.3 (#142246)
- remove some cruft from configure.in

* Wed Oct 20 2004 Nils Philippsen <nphilipp@redhat.com> 0.8.15-1
- include all languages (#136460)

* Tue Oct 12 2004 Nils Philippsen <nphilipp@redhat.com> 0.8.14-1
- actually install nonblockingreader module (#135445)

* Mon Oct 11 2004 Nils Philippsen <nphilipp@redhat.com> 0.8.12-1
- really update UI when reading from pipes (#120579, #135215)

* Fri Oct 08 2004 Nils Philippsen <nphilipp@redhat.com> 0.8.11-1
- fix gtk.main*() related DeprecationWarnings (#134978)

* Fri Oct 01 2004 Daniel J Walsh <dwalsh@redhat.com> 0.8.10-1
- Update translations

* Mon Sep 27 2004 Nils Philippsen <nphilipp@redhat.com> - 0.8.9-1
- enable Arabic translation (#133722)

* Thu Sep 23 2004 Nils Philippsen <nphilipp@redhat.com> - 0.8.8.1-1
- get in updated translations (#133137)
- appease make distcheck
- pick up updated autofoo scripts

* Wed Jun 16 2004 Brent Fox <bfox@redhat.com> - 0.8.8-9
- use watch cursor when starting and stopping services (bug #122425)

* Mon Apr 12 2004 Brent Fox <bfox@redhat.com> 0.8.8-8
- fix icon path (bug #120184)

* Tue Apr  6 2004 Brent Fox <bfox@redhat.com> 0.8.8-7
- remove extra strip (bug #119624)

* Mon Apr  5 2004 Brent Fox <bfox@redhat.com> 0.8.8-6
- code around new verbosity in libglade (bug #119622)

* Wed Mar 31 2004 Brent Fox <bfox@redhat.com> 0.8.8-5
- fix typo (bug #119559)

* Wed Mar 24 2004 Brent Fox <bfox@redhat.com> 0.8.8-4
- increase default size of the main window

* Fri Mar 19 2004 Brent Fox <bfox@redhat.com> 0.8.8-3
- make app exit properly on window close (bug #118762)

* Wed Mar 17 2004 Brent Fox <bfox@redhat.com> 0.8.8-2
- bump release

* Tue Mar 16 2004 Brent Fox <bfox@redhat.com> 0.8.8-1
- work around problem with libglade

* Wed Mar  3 2004 Brent Fox <bfox@redhat.com> 0.8.7-2
- add a BuildRequires on automake17

* Tue Mar  2 2004 Brent Fox <bfox@redhat.com> 0.8.7-1
- remove dependency on gnome-python2 and gnome-python2-canvas
- try to load glade file in the cwd, if not, pull from /usr/share/
- apply patch from bug #117277

* Tue Jan 6 2004 Daniel J Walsh <dwalsh@redhat.com> 0.8.6-3
- Fix console app so it launches properly

* Tue Jan 6 2004 Daniel J Walsh <dwalsh@redhat.com> 0.8.6-2
- remove requirement for 2.2

* Thu Nov 11 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.6-1
- Rename system-config-services

* Wed Oct 17 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-23
- Add all translated languages

* Fri Oct 17 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-22
- Remove /dev/null from status

* Mon Oct 6 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-21
- Fix crash on about

* Wed Oct 1 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-20
- bump

* Wed Oct 1 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-19
- Fix pathing problem on Hammer

* Fri Sep 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-18
- bump

* Fri Sep 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-17
- bump
* Fri Sep 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-16
- Eliminate debugging message

* Mon Aug 25 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-15
-  For some reason this did not make it to RHN Trying again. By Bumping version.

* Tue Aug 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-14
- Bumped version for rhl

* Tue Aug 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-13
- Remove depracated call

* Wed Jul 30 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-12
- Bumped version for rhl

* Wed Jul 30 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-11
- Changed handling of xinetd services to show xinetd service status

* Wed Jul 30 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-10
- Bumped version for rhl

* Tue Jul 29 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-9
- Allow services to have ':'s in them.

* Wed Jul 9 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-8
- Bumped version for rhl

* Wed Jul 9 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-7
- Add ability to add and delete services

* Tue Jun 17 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-6
- Bumped version for rhel

* Thu Jun 5 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-5
- Minor fixes to match GUI users guide and fix icon

* Tue May  27 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-4
- Bumped version for rhel

* Tue May  27 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-3
- Moved system-config-service.png to /usr/share/system-config-services

* Fri Mar  7 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-2
- Bumped version for rhel

* Tue Mar  4 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.5-1
- Fix swiching runlevels on modified screens.

* Tue Feb  25 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.4-2
- Fix dissapearing text on selecting toggle.

* Tue Jan  28 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.4-1
- Release Candidate
- Fix Icon

* Tue Jan  28 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-12
- Fix Language Problems

* Tue Jan  28 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-11
- Fix handling of errors in /etc/init.d directory

* Tue Jan  14 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-10
- Update documentation

* Thu Jan  9 2003 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-9
- Added StartupNotify=true
- Added accellerators

* Thu Dec  12 2002 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-8
- Update help docs

* Fri Dec  6 2002 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-7
- Fix error catching on invalid display

* Tue Dec  3 2002 Daniel J Walsh <dwalsh@redhat.com> 0.8.3-6
- Fix DISPLAY error handling
- Stretch Screen size
- Update status box after Start/Stop/Restart
- Fix Icon error

* Thu Nov 14 2002 Dan Walsh <dwalsh@redhat.com> 0.8.3-5
- Fix reading of descriptions from startup scripts to ignore blank lines

* Thu Nov 14 2002 Dan Walsh <dwalsh@redhat.com> 0.8.3-4
- Add scrollbar to description and status

* Thu Oct 24 2002 Dan Walsh <dwalsh@redhat.com> 0.8.3-3
- Fix internal handling of version number.

* Thu Oct 10 2002 Dan Walsh <dwalsh@redhat.com> 0.8.3-2
- Remove buttons from screen to match GNOME standards

* Tue Oct 1 2002 Dan Walsh <dwalsh@redhat.com> 0.8.3-1
- Change GUI Presentation and add service status

* Wed Sep 4 2002 Bill Nottingham <notting@redhat.com> 0.8.2-1
- fix startup in some locales

* Tue Sep 3 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-13
- Update translations

* Tue Aug 27 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-12
- Update translations
- Fix multi-processor problem with popen

* Tue Aug 20 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-11
- Use gnome url_show for help
- fix legal notice

* Mon Aug 19 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-10
- Fix word wrap
- Fix initial startup to select first row
- Update languages

* Sat Aug 10 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-9
- eliminate extra python files not intended for release

* Wed Aug 7 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-8
- Update dependencies

* Mon Aug 5 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-7
- Updated internationalization stuff

* Wed Jul 31 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-6
- Updated internationalization stuff

* Fri Jul 26 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-5
- Updated to use intltool and new build environment.
- Added with pam changes for timestamp
- New internationalization stuff

* Tue Jul 23 2002 Dan Walsh <dwalsh@redhat.com>
- Fix the desktop file, using new naming standards.
- Fix the error outpur

* Mon Jul 22 2002 Dan Walsh <dwalsh@redhat.com>
- Fix clock cursor, set app insensitive until services loaded"

* Mon Jul 22 2002 Tammy Fox <tfox@redhat.com>
- Updated docs

* Wed Jul  17 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-1
- Fix internationalization problems.  Clean up glade port.

* Thu Jul  11 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-1
- complete rename to system-config-services

* Tue Jul  9 2002 Dan Walsh <dwalsh@redhat.com> 0.8.1-1
- complete gtk2 port, Fix Help, About, fix minor bugs

* Wed May 29 2002 Bill Nottingham <notting@redhat.com> 0.8.0-1
- initial hack gtk2 port

* Mon Apr 15 2002 Trond Eivind Glomsrød <teg@redhat.com> 0.7.0-3
- Update translations

* Wed Apr 10 2002 Bill Nottingham <notting@redhat.com> 0.7.0-2
- fix docs (#63179)

* Tue Apr  9 2002 Bill Nottingham <notting@redhat.com>
- add some more cases to #60384 fix

* Sun Apr  7 2002 Jeremy Katz <katzj@redhat.com>
- don't show rpmsave, rpmnew, rpmorig, or .swp files (#60384)

* Tue Apr  2 2002 Nalin Dahyabhai <nalin@redhat.com>
- set up userhelper for system-config-services

* Fri Jan 25 2002 Bill Nottingham <notting@redhat.com>
- add patch to fix startup when there are services with 'hide' set

* Fri Aug 24 2001 Tim Powers <timp@redhat.com>
- fixed typo in Requires /;sbin/chkconfig

* Fri Aug 24 2001 Bill Nottingham <notting@redhat.com>
- build with new translations
- move system-config-services link to /usr/bin

* Fri Aug 17 2001 Bill Nottingham <notting@redhat.com>
- translation typos (#51774, #51776)
- add system-config-services link
- if we're using find_lang, don't specify the .mo files explicitly

* Mon Aug 13 2001 Tim Powers <timp@redhat.com>
- updated serviceconf.gladestrings

* Fri Aug 10 2001 Tim Powers <timp@redhat.com>
- languified specfile for additional translations

* Thu Aug  9 2001 Alexander Larsson <alexl@redhat.com> 0.6.1-1
- Add an icon

* Thu Aug  9 2001 Alexander Larsson <alexl@redhat.com>
- Install in sysconfig.

* Tue Aug  7 2001 Tim Powers <timp@redhat.com>
- gnomified
- work around parsing languified chkconfig output so that we can get accurate information displayed

* Tue Jul 31 2001 Tim Powers <timp@redhat.com>
- languified since we now serve multiple languages

* Mon Jul 30 2001 Yukihiro Nakai <ynakai@redhat.com>
- User %%fine_lang
- Add Japanese translation.

* Mon Jul 30 2001 Preston Brown <pbrown@redhat.com>
- clean up title display
- make sure initial highlighted entry also displays description info

* Wed Jul 18 2001 Tammy Fox <tfox@redhat.com>
- added help doc
- moved man page into man directory
- added Makefile for man page
- added man page to spec file

* Mon Jul  9 2001 Tim Powers <timp@redhat.com>
- languify to shutup rpmlint

* Thu Jul  5 2001 Tim Powers <timp@redhat.com>
- removed TODO and README, added COPYING file to docs

* Tue May 15 2001 Tim Powers <timp@redhat.com>
- Initial build.


