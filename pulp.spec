# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

%if 0%{?rhel} == 5
%define pulp_selinux 0
%else
%define pulp_selinux 1
%endif

%if %{pulp_selinux}
#SELinux 
%define selinux_variants mls strict targeted
%define selinux_policyver %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2> /dev/null)
%define modulename pulp
%define moduletype apps
%endif

# -- headers - pulp server ---------------------------------------------------

Name:           pulp
Version:        0.0.224
Release:        1%{?dist}
Summary:        An application for managing software content

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/pulp/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-nose	
BuildRequires:  rpm-python
%if %{pulp_selinux}
BuildRequires:  checkpolicy, selinux-policy-devel, hardlink
%endif

Requires: %{name}-common = %{version}
Requires: pymongo >= 1.9
Requires: python-setuptools
Requires: python-webpy
Requires: python-simplejson >= 2.0.9
Requires: python-oauth2
Requires: python-httplib2
Requires: python-isodate >= 0.4.4
Requires: python-BeautifulSoup
Requires: grinder >= 0.0.110
Requires: httpd
Requires: mod_ssl
Requires: m2crypto
Requires: openssl
Requires: python-ldap
Requires: python-gofer >= 0.45
Requires: crontabs
Requires: acl
Requires: mod_wsgi = 3.2-3.sslpatch%{?dist}
Requires: mongodb
Requires: mongodb-server
Requires: qpid-cpp-server

%if %{pulp_selinux}
%if "%{selinux_policyver}" != ""
Requires: selinux-policy >= %{selinux_policyver}
%endif
Requires(post): /usr/sbin/semodule, /sbin/fixfiles
Requires(postun): /usr/sbin/semodule
%endif

%if 0%{?rhel} == 5
# RHEL-5
Requires: python-uuid
Requires: python-ssl
Requires: python-ctypes
Requires: python-hashlib
Requires: createrepo = 0.9.8-3
%endif
%if 0%{?rhel} == 6
# RHEL-6
Requires: python-ctypes
Requires: python-hashlib
Requires: nss >= 3.12.9
Requires: curl => 7.19.7
%endif

# newer pulp builds should require same client version
Requires: %{name}-consumer >= %{version}
Requires: %{name}-admin >= %{version}

# Both attempt to serve content at the same apache alias, so don't
# allow them to be installed at the same time.
Conflicts:      pulp-cds

%description
Pulp provides replication, access, and accounting for software repositories.

# -- headers - pulp client lib ---------------------------------------------------

%package client-lib
Summary:        Client side libraries pulp client tools
Group:          Development/Languages
BuildRequires:  rpm-python
Requires:       python-simplejson
Requires:       python-isodate >= 0.4.4
Requires:       m2crypto
Requires:       %{name}-common = %{version}
Requires:       gofer >= 0.45
%if !0%{?fedora}
# RHEL
Requires:       python-hashlib
%endif
Requires:       python-rhsm >= 0.96.4
Obsoletes:      pulp-client <= 0.218

%description client-lib
A collection of libraries used by by the pulp client tools. 

# -- headers - pulp client ---------------------------------------------------

%package consumer
Summary:        Client side tool for pulp consumers
Group:          Development/Languages
Requires:       %{name}-client-lib = %{version}
Obsoletes:      pulp-client <= 0.218

%description consumer
A client tool used on pulp consumers to do things such as consumer
registration, and repository binding.

# -- headers - pulp admin ---------------------------------------------------

%package admin
Summary:        Admin tool to administer the pulp server
Group:          Development/Languages
Requires:       %{name}-client-lib = %{version}
Obsoletes:      pulp-client <= 0.218

%description admin
A tool used to administer the pulp server, such as repo creation and synching,
and to kick off remote actions on consumers.

# -- headers - pulp common ---------------------------------------------------

%package common
Summary:        Pulp common python packages.
Group:          Development/Languages
BuildRequires:  rpm-python

%description common
A collection of resources that are common between the pulp server and client.

# -- headers - pulp cds ------------------------------------------------------

%package cds
Summary:        Provides the ability to run as a pulp external CDS.
Group:          Development/Languages
BuildRequires:  rpm-python
Requires:       %{name}-common = %{version}
Requires:       gofer >= 0.45
Requires:       grinder
Requires:       httpd
Requires:       mod_wsgi = 3.2-3.sslpatch%{?dist}
Requires:       mod_ssl
Requires:       m2crypto

%if %{pulp_selinux}
%if "%{selinux_policyver}" != ""
Requires: selinux-policy >= %{selinux_policyver}
%endif
Requires(post): /usr/sbin/semodule, /sbin/fixfiles
Requires(postun): /usr/sbin/semodule
%endif

# Both attempt to serve content at the same apache alias, so don't
# allow them to be installed at the same time.
Conflicts:      pulp

%description cds
Tools necessary to interact synchronize content from a pulp server and serve that content
to clients.

# -- build -------------------------------------------------------------------

%prep
%setup -q

%build
pushd src
%{__python} setup.py build
popd
%if %{pulp_selinux}
# SELinux Configuration
cd selinux
perl -i -pe 'BEGIN { $VER = join ".", grep /^\d+$/, split /\./, "%{version}.%{release}"; } s!\@\@VERSION\@\@!$VER!g;' %{modulename}.te
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
    mv %{modulename}.pp %{modulename}.pp.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -
%endif


%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd

# Pulp Configuration
mkdir -p %{buildroot}/etc/pulp
cp -R etc/pulp/* %{buildroot}/etc/pulp

# Pulp Log
mkdir -p %{buildroot}/var/log/pulp

# Apache Configuration
mkdir -p %{buildroot}/etc/httpd/conf.d/
cp etc/httpd/conf.d/pulp.conf %{buildroot}/etc/httpd/conf.d/

# Pulp Web Services
cp -R srv %{buildroot}

# Pulp PKI
mkdir -p %{buildroot}/etc/pki/pulp
mkdir -p %{buildroot}/etc/pki/consumer
cp etc/pki/pulp/* %{buildroot}/etc/pki/pulp

mkdir -p %{buildroot}/etc/pki/content

# Pulp Runtime
mkdir -p %{buildroot}/var/lib/pulp
mkdir -p %{buildroot}/var/lib/pulp/published
mkdir -p %{buildroot}/var/www
ln -s /var/lib/pulp/published %{buildroot}/var/www/pub

# Client and CDS Gofer Plugins
mkdir -p %{buildroot}/etc/gofer/plugins
mkdir -p %{buildroot}/usr/lib/gofer/plugins
cp etc/gofer/plugins/*.conf %{buildroot}/etc/gofer/plugins
cp -R src/pulp/client/consumer/goferplugins/*.py %{buildroot}/usr/lib/gofer/plugins
cp src/pulp/cds/gofer/cdsplugin.py %{buildroot}/usr/lib/gofer/plugins

# profile plugin
mkdir -p %{buildroot}/etc/yum/pluginconf.d/
mkdir -p %{buildroot}/usr/lib/yum-plugins/
cp etc/yum/pluginconf.d/*.conf %{buildroot}/etc/yum/pluginconf.d/
cp src/pulp/client/yumplugin/pulp-profile-update.py %{buildroot}/usr/lib/yum-plugins/

# Pulp and CDS init.d
mkdir -p %{buildroot}/etc/rc.d/init.d
cp etc/rc.d/init.d/* %{buildroot}/etc/rc.d/init.d/
if [ ! -e %{buildroot}/etc/rc.d/init.d/pulp-agent ]
then
    ln -s etc/rc.d/init.d/goferd %{buildroot}/etc/rc.d/init.d/pulp-agent
fi

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/%{name}*.egg-info

# Touch ghost files (these won't be packaged)
mkdir -p %{buildroot}/etc/yum.repos.d
touch %{buildroot}/etc/yum.repos.d/pulp.repo

# Pulp CDS
# This should match what's in gofer_cds_plugin.conf and pulp-cds.conf
mkdir -p %{buildroot}/var/lib/pulp-cds/repos
mkdir -p %{buildroot}/var/lib/pulp-cds/packages

# Pulp CDS Logging
mkdir -p %{buildroot}/var/log/pulp-cds

# Apache Configuration
mkdir -p %{buildroot}/etc/httpd/conf.d/
cp etc/httpd/conf.d/pulp-cds.conf %{buildroot}/etc/httpd/conf.d/

%if %{pulp_selinux}
# Install SELinux policy modules
cd selinux
for selinuxvariant in %{selinux_variants}
  do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 %{modulename}.pp.${selinuxvariant} \
           %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp
  done
# Install SELinux interfaces
install -d %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}
install -p -m 644 %{modulename}.if \
  %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if

# Hardlink identical policy module packages together
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux
cd -
%endif


%clean
rm -rf %{buildroot}

# -- post - pulp server ------------------------------------------------------

%post
setfacl -m u:apache:rwx /etc/pki/content/
%if %{pulp_selinux}
if /usr/sbin/selinuxenabled ; then
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp &> /dev/null || :
    done
fi
%endif
# -- post - pulp cds ---------------------------------------------------------

%post cds
setfacl -m u:apache:rwx /etc/pki/content/

# Create the cluster related files and give them Apache ownership;
# both httpd (apache) and gofer (root) will write to them, so to prevent
# permissions issues put them under apache
touch /var/lib/pulp-cds/.cluster-members-lock
touch /var/lib/pulp-cds/.cluster-members

chown apache:apache /var/lib/pulp-cds/.cluster-members-lock
chown apache:apache /var/lib/pulp-cds/.cluster-members

%if %{pulp_selinux}
if /usr/sbin/selinuxenabled ; then
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp &> /dev/null || :
    done
fi
%endif

# -- post - pulp consumer ------------------------------------------------------

%post consumer
pushd %{_sysconfdir}/rc.d/init.d
if [ "$1" = "1" ]; then
  ln -s goferd pulp-agent
fi
popd

%postun
# Clean up after package removal
%if %{pulp_selinux}
if [ $1 -eq 0 ]; then
  for selinuxvariant in %{selinux_variants}
    do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename}
    done
fi
%endif

%postun consumer
if [ "$1" = "0" ]; then
  rm -f %{_sysconfdir}/rc.d/init.d/pulp-agent
fi

%postun cds
# Clean up after package removal
%if %{pulp_selinux}
if [ $1 -eq 0 ]; then
  for selinuxvariant in %{selinux_variants}
    do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename}
    done
fi
%endif

# -- files - pulp server -----------------------------------------------------

%files
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/server/
%{python_sitelib}/pulp/repo_auth/
%config %{_sysconfdir}/pulp/pulp.conf
%config %{_sysconfdir}/pulp/repo_auth.conf
%config %{_sysconfdir}/pulp/logging
%config %{_sysconfdir}/httpd/conf.d/pulp.conf
%ghost %{_sysconfdir}/yum.repos.d/pulp.repo
%attr(775, apache, apache) %{_sysconfdir}/pulp
%attr(775, apache, apache) /srv/pulp
%attr(750, apache, apache) /srv/pulp/webservices.wsgi
%attr(750, apache, apache) /srv/pulp/bootstrap.wsgi
%attr(750, apache, apache) /srv/pulp/repo_auth.wsgi
%attr(3775, apache, apache) /var/lib/pulp
%attr(3775, apache, apache) /var/www/pub
%attr(3775, apache, apache) /var/log/pulp
%attr(3775, root, root) %{_sysconfdir}/pki/content
%attr(3775, root, root) %{_sysconfdir}/rc.d/init.d/pulp-server
%{_sysconfdir}/pki/pulp/ca.key
%{_sysconfdir}/pki/pulp/ca.crt
%if %{pulp_selinux}
# SELinux
%doc selinux/%{modulename}.fc selinux/%{modulename}.if selinux/%{modulename}.te
%{_datadir}/selinux/*/%{modulename}.pp
%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if
%endif
# -- files - common ----------------------------------------------------------

%files common
%defattr(-,root,root,-)
%doc
%{python_sitelib}/pulp/__init__.*
%{python_sitelib}/pulp/common/

# -- files - pulp client lib -----------------------------------------------------

%files client-lib
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/client/api
%{python_sitelib}/pulp/client/lib
%{python_sitelib}/pulp/client/pluginlib
%{python_sitelib}/pulp/client/plugins
%{python_sitelib}/pulp/client/*.py*

# -- files - pulp client -----------------------------------------------------

%files consumer
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/client/consumer
%{_bindir}/pulp-consumer
%{_exec_prefix}/lib/gofer/plugins/*.py*
%{_prefix}/lib/yum-plugins/pulp-profile-update.py*
%{_sysconfdir}/gofer/plugins/pulpplugin.conf
%{_sysconfdir}/gofer/plugins/consumer.conf
%{_sysconfdir}/yum/pluginconf.d/pulp-profile-update.conf
%attr(755,root,root) %{_sysconfdir}/pki/consumer/
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/yum/pluginconf.d/pulp-profile-update.conf
%config(noreplace) %{_sysconfdir}/pulp/consumer/consumer.conf
%ghost %{_sysconfdir}/rc.d/init.d/pulp-agent

# -- files - pulp admin -----------------------------------------------------

%files admin
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/client/admin
%{_bindir}/pulp-admin
%{_bindir}/pulp-migrate
%config(noreplace) %{_sysconfdir}/pulp/admin/admin.conf
%config(noreplace) %{_sysconfdir}/pulp/admin/task.conf
%config(noreplace) %{_sysconfdir}/pulp/admin/job.conf

# -- files - pulp cds --------------------------------------------------------

%files cds
%defattr(-,root,root,-)
%doc
%{python_sitelib}/pulp/cds/
%{python_sitelib}/pulp/repo_auth/
%{_sysconfdir}/gofer/plugins/cdsplugin.conf
%{_exec_prefix}/lib/gofer/plugins/cdsplugin.*
%attr(775, apache, apache) /srv/pulp
%attr(750, apache, apache) /srv/pulp/cds.wsgi
%config %{_sysconfdir}/httpd/conf.d/pulp-cds.conf
%config %{_sysconfdir}/pulp/cds.conf
%config %{_sysconfdir}/pulp/repo_auth.conf
%attr(3775, root, root) %{_sysconfdir}/pki/content
%attr(3775, root, root) %{_sysconfdir}/rc.d/init.d/pulp-cds
%attr(3775, apache, apache) /var/lib/pulp-cds
%attr(3775, apache, apache) /var/lib/pulp-cds/repos
%attr(3775, apache, apache) /var/lib/pulp-cds/packages
%attr(3775, apache, apache) /var/log/pulp-cds
%if %{pulp_selinux}
# SELinux
%doc selinux/%{modulename}.fc selinux/%{modulename}.if selinux/%{modulename}.te
%{_datadir}/selinux/*/%{modulename}.pp
%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if
%endif

# -- changelog ---------------------------------------------------------------

%changelog
* Fri Aug 12 2011 Jeff Ortel <jortel@redhat.com> 0.0.224-1
- Align with gofer 0.45. (jortel@redhat.com)
- Update UG for CR15. (jortel@redhat.com)
- Update website to: CR15. (jortel@redhat.com)
- 717975 - discover urls with repodata as valid urls (pkilambi@redhat.com)
- if distribution is None dont set the url (pkilambi@redhat.com)
-  Remove Metadata: * util method to support modifyrepo --remove * api changes
  to support remove_metadata call * web services remove_metadata call * cli
  changes to support pulp-admin remove_metadata * unit tests
  (pkilambi@redhat.com)
- Bump grinder to 0.110 (jmatthews@redhat.com)
- 730102 - compute the kickstart url on server when showing the distribution
  list (pkilambi@redhat.com)
- Initial implementation of the type descriptors parser. Still need to flush
  out unit tests but I want to back it up now. (jason.dobies@redhat.com)
- 729099 - fixing help text for associate operations (pkilambi@redhat.com)
- Adding make tree option to dependency resolver (pkilambi@redhat.com)
- Disable deepcopy of self.cfg for now since it's completely unsupported on
  python 2.6 (jslagle@redhat.com)
- 721321 - Don't allow pulp and pulp-cds to be installed on the same box
  (jason.dobies@redhat.com)
- 691752 - Corrected the argument name in the error text
  (jason.dobies@redhat.com)
- Adding ability to set the create flag on collection retrieval.
  (jason.dobies@redhat.com)

* Mon Aug 08 2011 Jeff Ortel <jortel@redhat.com> 0.0.223-1
- Save args as self.args so when it gets modified in setup(), the change is
  preserved (jslagle@redhat.com)
- 727906 - Added input validation and error message with a correct format for
  notes input. (skarmark@redhat.com)
* Fri Aug 05 2011 Pradeep Kilambi <pkilambi@redhat.com> 0.0.222-1
- bumping grinder requires (pkilambi@redhat.com)
- fixing file sync imports (pkilambi@redhat.com)
- 728579 - Fix errata install broken during jobs migration. (jortel@redhat.com)
- fix typo (jmatthews@redhat.com)
- Cancel sync enhancements for local sync as well as interrupting createrepo
  (jmatthews@redhat.com)
- Adding ability to cancel a running createrepo process (jmatthews@redhat.com)
- 642654 fix another reference to create (jslagle@redhat.com)
- 642654 Rename consumer create/delete to register/unregister
  (jslagle@redhat.com)
- Change wording about consumer creation and don't show it if the user is
  already running consumer create (jslagle@redhat.com)
- remove unused setup_client method (jslagle@redhat.com)

* Thu Aug 04 2011 Jeff Ortel <jortel@redhat.com> 0.0.221-1
- Update client (yum) code to make idempotent. Rewrite Package.install() so
  package install will not raise TransactionError when a package is already
  installed.  Also, changed API to no longer need (or accept) package names
  explicitly parsed into name, arch for arch specific matching.
  (jortel@redhat.com)
- Fix plugin directories in the configurations (jslagle@redhat.com)

* Wed Aug 03 2011 Jeff Ortel <jortel@redhat.com> 0.0.220-1
- Enqueue package install tasks, non-unique. (jortel@redhat.com)
- renamed file manifest to match cdn (pkilambi@redhat.com)
- 727900 - file status (pkilambi@redhat.com)

* Wed Aug 03 2011 Jeff Ortel <jortel@redhat.com> 0.0.219-1
- Requires gofer 0.44. (jortel@redhat.com)
- 695607 - Fix RHEL macros.  Clean up merge artifacts in changelog.
  (jortel@redhat.com)
- Add support for asynchronous RMI timeouts using gofer 0.44 watchdog.
  (jortel@redhat.com)
- 726706 - Error in repo sync schedule error message (jmatthews@redhat.com)
- Fix syntax error in if stmt (jslagle@redhat.com)
- Only link pulp-agent to goferd init script if it doesn't exist already
  (jslagle@redhat.com)
- 727666 - fixed unpickling of private methods (jconnor@redhat.com)
- 727666 - not a fix, added instrumentation to code that raises a
  SnapshotFailure exception when the lookup of a pickled method on a class
  occurs much more informative than the UnboundLocalError that was being raised
  (jconnor@redhat.com)
- Client refactoring to support generic content. (jslagle@redhat.com)
- Require grinder .109 for quicker cancel syncs (jmatthews@redhat.com)
- Rename gofer dir to goferplugins to avoid name conflict with the installed
  gofer module (jslagle@redhat.com)
- Fix current() task management in AsyncTask. (jortel@redhat.com)
- Add missing repository_api (jslagle@redhat.com)
- Bump obsoletes version of pulp-client to 218 (jslagle@redhat.com)
- More updates for client->consumer rename (jslagle@redhat.com)
- Rename pulp-client -> pulp-consumer (jslagle@redhat.com)
- Task plugin should be disabled by default (jslagle@redhat.com)
- 723663 - minor help fixes (pkilambi@redhat.com)
- SELinux changes for pulp-cds (jmatthews@redhat.com)
- pulp.spec will only install selinux files on fedora/el6
  (jmatthews@redhat.com)
- SELinux changes for RHEL-5 (jmatthews@redhat.com)
- 726782 - added missing arch update information to delta (skarmark@redhat.com)
- Update spec file for client refactoring packaging (jslagle@redhat.com)
- Wire up consumer commands as plugins (jslagle@redhat.com)
- Remove core module (jslagle@redhat.com)
- Merge core.utils and lib.utils into a single utils module
  (jslagle@redhat.com)
- Reorginazations: client.lib.plugin_lib -> client.pluginlib and
  client.lib.plugins -> client.plugins (jslagle@redhat.com)
- Admin refactorings to support plugins, add auth as first plugin
  (jslagle@redhat.com)
- Reorganize modules amoung admin/consumer clients (jslagle@redhat.com)

* Fri Jul 29 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.218-1
- changed the name of the timeout field to timeout_delta in _pickled_fields
  (jconnor@redhat.com)
- 679764 - added cloning status, if present along with sync status under repo
  status (skarmark@redhat.com)
- 726709 - Resolved name conflict between timeout field and timeout method of
  Task class (jconnor@redhat.com)
- manifest generate support for files (pkilambi@redhat.com)

* Thu Jul 28 2011 Jeff Ortel <jortel@redhat.com> 0.0.217-1
- Fix package install. (jortel@redhat.com)

* Wed Jul 27 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.216-1
- fixed typo (jconnor@redhat.com)

* Wed Jul 27 2011 Jeff Ortel <jortel@redhat.com> 0.0.215-1
- skip tag used on rhui branch. (jortel@redhat.com)
- Bump to gofer 0.43 for project alignment. (jortel@redhat.com)
- Fix printed summary on package install on consumer group. (jortel@redhat.com)
- Add job debugging CLI command to pulp-admin. (jortel@redhat.com)
- bumping grinder version (pkilambi@redhat.com)
- 713507 - API and cli changes for RFE: querying repos by notes field
  (skarmark@redhat.com)
- adding content type to repo list output (pkilambi@redhat.com)
- Refit package install/errata on consumer group to use jobs.
  (jortel@redhat.com)
- Merge branch 'master' of ssh://git.fedorahosted.org/git/pulp
  (skarmark@redhat.com)
- moving content_type help out of schedule area (pkilambi@redhat.com)
- added logging for duplicate importers and distributors (jconnor@redhat.com)
- added support for per-plugin toggling of importers and distributors in the
  main pulp configuration file (jconnor@redhat.com)
- Repogroup update changes This change includes changes to repo update
  consolidating all parameters of update in delta instead of calling separate
  update calls. This also includes removing symlink update from repo update and
  repogroup update, fixing repo sync schedule update as well.
  (skarmark@redhat.com)

* Fri Jul 22 2011 Jeff Ortel <jortel@redhat.com> 0.0.213-1
- Change package & packagegroup install on consumer to synchronous RMI.
  (jortel@redhat.com)
- SElinux first steps, auth login/logout, repo create/sync/delete
  (jmatthews@redhat.com)
- Added Importer and Distributor base classes (jconnor@redhat.com)
- Moving the pushcount migration from 17 to 22 to account for latest fix
  (pkilambi@redhat.com)
- Added first pass at generic content plugin manager (jconnor@redhat.com)
- Skeleton for server-side content plugins and framework (jconnor@redhat.com)
- Fixing pushcount to convert to int before storing in db (pkilambi@redhat.com)
- 714046 - fixed error message for admin user deletion (skarmark@redhat.com)
- Fixing key-value attributes api bug when creating a consumer
  (skarmark@redhat.com)

* Wed Jul 20 2011 Jeff Ortel <jortel@redhat.com> 0.0.212-1
- Add Task.job_id to support job concept in task subsystem. (jortel@redhat.com)
- Pulp synchronizer implementation to support generic content types and file
  based sync support: (pkilambi@redhat.com)
- 719651 - fixing the ldap check during authentication (pkilambi@redhat.com)
- fixing selective sync to use updated depsolver api changes
  (pkilambi@redhat.com)
- fixing consumer create to use new put call (pkilambi@redhat.com)
- fixing pulp to pass in proxy settings correctly to grinder
  (pkilambi@redhat.com)
- turning the valid filters into a tuple (jconnor@redhat.com)
- moving the GET package profile call to same class to match the url requests
  (pkilambi@redhat.com)
- Changing the package profile update from POST to PUT (pkilambi@redhat.com)

* Fri Jul 15 2011 Jeff Ortel <jortel@redhat.com> 0.0.210-1
- 722521 change --wait option to --nowait to restore previous behavior
  (jslagle@redhat.com)
- Expose Heartbeat.send() on agent as RMI for debugging.
  (jortel@redhat.com)

* Thu Jul 14 2011 Jeff Ortel <jortel@redhat.com> 0.0.209-1
- typo in conf file (jconnor@redhat.com)
- added config option to toggle auditing (jconnor@redhat.com)
- Check for None auth before trying to remove emtpy basic http authorization
  (jslagle@redhat.com)
- Switch to using append option instead of merge.  merge is not available on
  rhel 5's apache (jslagle@redhat.com)
* Thu Jul 14 2011 Jeff Ortel <jortel@redhat.com> 0.0.208-1
- Incremented to match latest RHUI version (jortel@redhat.com)

* Thu Jul 14 2011 Jeff Ortel <jortel@redhat.com> 0.0.207-1
- Fix reference to field variable (jslagle@redhat.com)
- Adding script to display mongodb file space usage statistics
  (jmatthews@redhat.com)
- Updated pulpproject.org index to fix updated Pulp BZ Category -> Community
  (tsanders@tsanders-x201.(none))
- 709500 Add a command line option --wait that can specify if the user wants to
  wait for the package install to finish or not.  If the consumer is
  unavailable, confirm the wait option (jslagle@redhat.com)
- Bump website to CR14. (jortel@redhat.com)
- 721021 remove empty Basic auth from end of authorization header if specified
  (jslagle@redhat.com)
- Changing the result datastructure to be a dictionary of {dep:[pkgs]} fit
  katello's needs (pkilambi@redhat.com)

* Tue Jul 12 2011 Jeff Ortel <jortel@redhat.com> 0.0.206-1
- removing mongo 1.7.5 restriction on pulp f15 (pkilambi@redhat.com)
* Mon Jul 11 2011 Jeff Ortel <jortel@redhat.com> 0.0.205-1
- Fix check for basic auth (jslagle@redhat.com)
- Add a header that sets a blank Basic authorization for every request, needed
  for repo auth.  Remove the blank authorization when validating from the API
  side. (jslagle@redhat.com)
- changing local syncs to account for all metadata (pkilambi@redhat.com)
- Add dist to required relase for mod_wsgi (jslagle@redhat.com)
- Add required mod_wsgi to spec file (jslagle@redhat.com)
- Automatic commit of package [mod_wsgi] minor release [3.2-3.sslpatch].
  (jslagle@redhat.com)
- check metadata preservation when add/remove on repositories
  (pkilambi@redhat.com)
- Adding checks to see if repo has metadata preserved before regenerating
  (pkilambi@redhat.com)
- 719955 - log.info is trying to print an entire repo object instead of just
  the id spamming the pulp logs during delete (pkilambi@redhat.com)
- 703878 - RFE: Exposing the unresolved dependencies  in the package dependency
  result (pkilambi@redhat.com)
- Make same repo_auth changes for pulp cds (jslagle@redhat.com)
- Update pulp.spec to install repo_auth.wsgi correctly and no longer need to
  uncomment lines for mod_python (jslagle@redhat.com)
- Move repo_auth.wsgi to /srv (jslagle@redhat.com)
- 696669 fix unit tests for oid validation updates (jslagle@redhat.com)
- 696669 move repo auth to mod_wsgi access script handler and eliminate dep on
  mod_python (jslagle@redhat.com)
- fixing help (pkilambi@redhat.com)
- fixing exit messages to refer filetype as metadata type (pkilambi@redhat.com)
- Add missing wsgi.conf file (jslagle@redhat.com)
- Automatic commit of package [pulp] release [0.0.203-1]. (jslagle@redhat.com)
- Add mod_wsgi rpm build to pulp (jslagle@redhat.com)
- 669759 - typo, missing word "is" in schedule time is in past message
  (jmatthews@redhat.com)
- converted all auditing events to use utc (jconnor@redhat.com)
- added query parametes to GET method (jconnor@redhat.com)
- using $in for union and $all for intersection operations (jconnor@redhat.com)
- added collection query decorator (jconnor@redhat.com)
- gutted decorator to simply parse the query parameter and pass in a keyword
  filters argument (jconnor@redhat.com)
- added _ prefix to common query parameters (jconnor@redhat.com)
- fix issue downloading sqlite db metadata files (pkilambi@redhat.com)
- fixing help for download metadata (pkilambi@redhat.com)
- Add a helper mock function to testutil, also keeps track of all mocks to make
  sure everything is unmocked in tearDown (jslagle@redhat.com)
- make sure run_async gets unmocked (jslagle@redhat.com)
- Incremented to match latest rhui version (jason.dobies@redhat.com)
- 718287 - Pulp is inconsistent with what it stores in relative URL, so
  changing from a startswith to a find for the protected repo retrieval.
  (jason.dobies@redhat.com)
- Move towards using mock library for now since dingus has many python 2.4
  incompatibilities (jslagle@redhat.com)
- 715071 - lowering the log level during repo delete to debug
  (pkilambi@redhat.com)
- Update createrepo login in pulp to account for custom metadata; also rename
  the backup file before running modifyrepo to preserve the mdtype
  (pkilambi@redhat.com)
- renaming metadata call to generate_metadata (pkilambi@redhat.com)
- Custom Metadata support: (pkilambi@redhat.com)
- added args to returned serialized task (jconnor@redhat.com)
- converted timestamp to utc (jconnor@redhat.com)
- Refactor __del__ into a cancel_dispatcher method that is meant to be called
  (jslagle@redhat.com)
- Pulp now uses profile module from python-rhsm and requires it
  (pkilambi@redhat.com)
- added tzinfo to start and end dates (jconnor@redhat.com)
- added task cancel command (jconnor@redhat.com)
- changed cds history query to properly deal with iso8601 timestamps
  (jconnor@redhat.com)
- Importing python-rhsm source into pulp (pkilambi@redhat.com)
- 712083 - changing the error message to warnings (pkilambi@redhat.com)
- Adding a preserve metadata as an option at repo creation time. More info
  about feature  can be found at
  https://fedorahosted.org/pulp/wiki/PreserveMetadata (pkilambi@redhat.com)
- 715504 - Apache's error_log also generating pulp log messages
  (jmatthews@redhat.com)
- replacing query_by_bz and query_by_cve functions by advanced mongo queries
  for better performance and cleaner implementation (skarmark@redhat.com)
- Bump to gofer 0.42 (just to keep projects aligned). (jortel@redhat.com)
- added some ghetto date format validation (jconnor@redhat.com)
- converting expected iso8601 date string to datetime instance
  (jconnor@redhat.com)
- added iso8601 parsing and formating methods for date (only) instances
  (jconnor@redhat.com)
- errata enhancement api and cli changes for bugzilla and cve search
  (skarmark@redhat.com)
- 713742 - patch by Chris St. Pierre fixed improper rlock instance detection in
  get state for pickling (jconnor@redhat.com)
- 714046 - added login to string substitution (jconnor@redhat.com)
- added new controller for generic task cancelation (jconnor@redhat.com)
  (jason.dobies@redhat.com)
- Move repos under /var/lib/pulp-cds/repos so we don't serve packages straight
  up (jason.dobies@redhat.com)
- Tell grinder to use a single location for package storage.
  (jason.dobies@redhat.com)
- converting timedelta to duration in order to properly format it
  (jconnor@redhat.com)
- 706953, 707986 - allow updates to modify existing schedule instead of having
  to re-specify the schedule in its entirety (jconnor@redhat.com)
- 709488 Use keyword arg for timeout value, and fix help messages for timeout
  values (jslagle@redhat.com)
- Added CDS sync history to CDS CLI API (jason.dobies@redhat.com)
- Added CLI API call for repo sync history (jason.dobies@redhat.com)
- changed scheduled task behavior to reset task states on enqueue instead of on
  run (jconnor@redhat.com)
- added conditional to avoid calling release on garbage collected lock
  (jconnor@redhat.com)
- only release the lock in the dispatcher on exit as we are no longer killing
  the thread on errors (jconnor@redhat.com)
- 691962 - repo clone should not clone files along with packages and errata
  (skarmark@redhat.com)
- adding id to repo delete error message to find culprit repo
  (skarmark@redhat.com)
- 714745 - added initial parsing call for start and end dates of cds history so
  that we convert a datetime object to local tz instead of a string
  (jconnor@redhat.com)
- 714691 - fixed type that caused params to resolve to an instance method
  instead of a local variable (jconnor@redhat.com)
- Cast itertools.chain to tuple so that it can be iterated more than once, it
  happens in both from_snapshot and to_snapshot (jslagle@redhat.com)
- 713493 - fixed auth login to relogin new credentials; will just replace
  existing user certs with new ones (pkilambi@redhat.com)
- Bump website to CR13. (jortel@redhat.com)
- Merge branch 'master' of ssh://git.fedorahosted.org/git/pulp
  (jslagle@redhat.com)
- 709500 Fix scheduling of package install using --when parameter
  (jslagle@redhat.com)
- Adding mongo 1.7.5 as a requires for f15 pulp build (pkilambi@redhat.com)
- 707295 - removed relativepath from repo update; updated feed update logic to
  check if relative path matches before allowing update (pkilambi@redhat.com)
- In a consumer case, password can be none, let it return the user
  (pkilambi@redhat.com)
- updated log config for rhel5, remove spaces from 'handlers'
  (jmatthews@redhat.com)
- Fix to work around http://bugs.python.org/issue3136 in python 2.4
  (jmatthews@redhat.com)
- Updates for Python 2.4 logging configuration file (jmatthews@redhat.com)
- Pulp logging now uses configuration file from /etc/pulp/logging
  (jmatthews@redhat.com)
- adding new createrepo as a dependency for el5 builds (pkilambi@redhat.com)
- 709514 - error message for failed errata install for consumer and
  consumergroup corrected (skarmark@redhat.com)
- Adding newer version of createrepo for pulp on el5 (pkilambi@redhat.com)
- Tell systemctl to ignore deps so that our init script works correctly on
  Fedora 15 (jslagle@redhat.com)
- 713183 - python 2.4 compat patch (pkilambi@redhat.com)
-  Patch from Chris St. Pierre <chris.a.st.pierre@gmail.com> :
  (pkilambi@redhat.com)
- 713580 - fixing wrong list.remove in blacklist filter application logic in
  repo sync (skarmark@redhat.com)
- 669520 python 2.4 compat fix (jslagle@redhat.com)
- 713176 - Changed user certificate expirations to 1 week. Consumer certificate
  expirations, while configurable, remain at the default of 10 years.
  (jason.dobies@redhat.com)
- bz# 669520 handle exception during compilation of invalid regular expression
  so that we can show the user a helpful message (jslagle@redhat.com)

* Thu Jul 07 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.204-1
- Update pulp.spec to install repo_auth.wsgi correctly and no longer need to
  uncomment lines for mod_python (jslagle@redhat.com)
- Move repo_auth.wsgi to /srv (jslagle@redhat.com)
- 696669 fix unit tests for oid validation updates (jslagle@redhat.com)
- 696669 move repo auth to mod_wsgi access script handler and eliminate dep on
  mod_python (jslagle@redhat.com)

* Thu Jul 07 2011 James Slagle <jslagle@redhat.com> 0.0.203-1
- Add mod_wsgi rpm build to pulp (jslagle@redhat.com)

* Wed Jul 06 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.202-1
- 669759 - typo, missing word "is" in schedule time is in past message
  (jmatthews@redhat.com)
- converted all auditing events to use utc (jconnor@redhat.com)
- wrong line (jconnor@redhat.com)
- added debugging log output (jconnor@redhat.com)
- bug in query params generation (jconnor@redhat.com)
- added query parametes to GET method (jconnor@redhat.com)
- using $in for union and $all for intersection operations (jconnor@redhat.com)
- stubbed out spec doc building calls (jconnor@redhat.com)
- added collectio query decorator (jconnor@redhat.com)
- gutted decorator to simply parse the query parameter and pass in a keyword
  filters argument (jconnor@redhat.com)
- added _ prefix to common query parameters (jconnor@redhat.com)
- fix issue downloading sqlite db metadata files (pkilambi@redhat.com)
- fixing help for download metadata (pkilambi@redhat.com)
- Add a helper mock function to testutil, also keeps track of all mocks to make
  sure everything is unmocked in tearDown (jslagle@redhat.com)
- make sure run_async gets unmocked (jslagle@redhat.com)
- Incremented to match latest rhui version (jason.dobies@redhat.com)
- 718287 - Pulp is inconsistent with what it stores in relative URL, so
  changing from a startswith to a find for the protected repo retrieval.
  (jason.dobies@redhat.com)
- Move towards using mock library for now since dingus has many python 2.4
  incompatibilities (jslagle@redhat.com)
- Merge branch 'master' into test-refactor (jslagle@redhat.com)
- 715071 - lowering the log level during repo delete to debug
  (pkilambi@redhat.com)
- Merge branch 'master' into test-refactor (jslagle@redhat.com)
- Add missing import (jslagle@redhat.com)
- Make import path asbsolute, so tests can be run from any directory
  (jslagle@redhat.com)
- Move needed dir from data into functional test dir (jslagle@redhat.com)
- update for testutil changes (jslagle@redhat.com)
- Update createrepo login in pulp to account for custom metadata; also rename
  the backup file before running modifyrepo to preserve the mdtype
  (pkilambi@redhat.com)
- Merge with master (jslagle@redhat.com)
- Add a test for role api (jslagle@redhat.com)
- tweaks to error handling around the client (pkilambi@redhat.com)
- Use PulpTest as base class here (jslagle@redhat.com)
- Example unit test using dingus for repo_sync.py (jslagle@redhat.com)
- Move these 2 test modules to functional tests dir (jslagle@redhat.com)
- Make each test set path to the common dir (jslagle@redhat.com)
- Move test dir cleanup to tearDown instead of clean since clean also gets
  called from setUp (jslagle@redhat.com)
- Merge with master (jslagle@redhat.com)
- Refactor all tests to use common PulpAsyncTest base class
  (jslagle@redhat.com)
- Use dingus for mocking instead of mox (jslagle@redhat.com)
- Use PulpTest instead of PulpAsyncTest for this test (jslagle@redhat.com)
- More base class refactorings, make sure tests that use PulpAsyncTest,
  shutdown the task queue correctly, this should solve our threading exception
  problems (jslagle@redhat.com)
- Refactor __del__ into a cancel_dispatcher method that is meant to be called
  (jslagle@redhat.com)
- Refactoring some of the testutil setup into a common base class to avoid
  repetition in each test module (also fixes erroneous connection to
  pulp_database) (jslagle@redhat.com)

* Fri Jul 01 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.201-1
- Bringing in line with latest Pulp build version (jason.dobies@redhat.com)

* Wed Jun 29 2011 Jeff Ortel <jortel@redhat.com> 0.0.200-1
- Custom Metadata Support (Continued): (pkilambi@redhat.com)
- fixing rhel5 issues in unit tests, disabled get test until I figure out an
  alternative to dump_xml on el5 (pkilambi@redhat.com)
- Custom Metadata support: (pkilambi@redhat.com)
- Temporarily remove the quick commands section until we decide how to best
  maintain it (jason.dobies@redhat.com)

* Fri Jun 24 2011 Jeff Ortel <jortel@redhat.com> 0.0.198-1
- added args to returned serialized task (jconnor@redhat.com)
- converted timestamp to utc (jconnor@redhat.com)
- Pulp now uses profile module from python-rhsm and requires it
  (pkilambi@redhat.com)
- removed test that fails due to bug in timezone support, 716243
  (jconnor@redhat.com)
- changed tests to insert iso8601 strings as time stamps (jconnor@redhat.com)
- added task cancel command (jconnor@redhat.com)
- added wiki comments and tied cancel task to a url (jconnor@redhat.com)
- changed cds history query to properly deal with iso8601 timestamps
  (jconnor@redhat.com)
- 712083 - changing the error message to warnings (pkilambi@redhat.com)
- Incremented to pass RHUI build (jason.dobies@redhat.com)
- Adding a preserve metadata as an option at repo creation time. More info
  about feature  can be found at
  https://fedorahosted.org/pulp/wiki/PreserveMetadata (pkilambi@redhat.com)
- 715504 - Apache's error_log also generating pulp log messages
  (jmatthews@redhat.com)
- replacing query_by_bz and query_by_cve functions by advanced mongo queries
  for better performance and cleaner implementation (skarmark@redhat.com)

* Wed Jun 22 2011 Jeff Ortel <jortel@redhat.com> 0.0.196-1
- Bump to gofer 0.42 (just to keep projects aligned). (jortel@redhat.com)
- Added some ghetto date format validation (jconnor@redhat.com)
- Converting expected iso8601 date string to datetime instance
  (jconnor@redhat.com)
- added iso8601 parsing and formating methods for date (only) instances
  (jconnor@redhat.com)

* Wed Jun 22 2011 Jeff Ortel <jortel@redhat.com> 0.0.195-1
- errata enhancement api and cli changes for bugzilla and cve search
  (skarmark@redhat.com)
- 713742 - patch by Chris St. Pierre fixed improper rlock instance detection in
  get state for pickling (jconnor@redhat.com)
- 714046 - added login to string substitution (jconnor@redhat.com)
- added new controller for generic task cancelation (jconnor@redhat.com)
- Automatic commit of package [pulp] release [0.0.194-1].
  (jason.dobies@redhat.com)
- Move repos under /var/lib/pulp-cds/repos so we don't serve packages straight
  up (jason.dobies@redhat.com)
- Merged in rhui version (jason.dobies@redhat.com)
- Tell grinder to use a single location for package storage.
  (jason.dobies@redhat.com)
- converting timedelta to duration in order to properly format it
  (jconnor@redhat.com)
- 706953, 707986 - allow updates to modify existing schedule instead of having
  to re-specify the schedule in its entirety (jconnor@redhat.com)
- 709488 - Use keyword arg for timeout value, and fix help messages for timeout
  values (jslagle@redhat.com)
- Added CDS sync history to CDS CLI API (jason.dobies@redhat.com)
- Remove unneeded log.error for translate_to_utf8 (jmatthews@redhat.com)
- Added CLI API call for repo sync history (jason.dobies@redhat.com)
- changed scheduled task behavior to reset task states on enqueue instead of on
  run (jconnor@redhat.com)
- 691962 - repo clone should not clone files along with packages and errata
  (skarmark@redhat.com)
- adding id to repo delete error message to find culprit repo
  (skarmark@redhat.com)
- 714745 - added initial parsing call for start and end dates of cds history so
  that we convert a datetime object to local tz instead of a string
  (jconnor@redhat.com)
- 714691 - fixed type that caused params to resolve to an instance method
  instead of a local variable (jconnor@redhat.com)
- Cast itertools.chain to tuple so that it can be iterated more than once, it
  happens in both from_snapshot and to_snapshot (jslagle@redhat.com)
- Automatic commit of package [pulp] release [0.0.192-1]. (jortel@redhat.com)
- 713493 - fixed auth login to relogin new credentials; will just replace
  existing user certs with new ones (pkilambi@redhat.com)
- Bump website to CR13. (jortel@redhat.com)
- 709500 Fix scheduling of package install using --when parameter
  (jslagle@redhat.com)
- Automatic commit of package [pulp] release [0.0.191-1]. (jortel@redhat.com)
- Adding mongo 1.7.5 as a requires for f15 pulp build (pkilambi@redhat.com)
- 707295 - removed relativepath from repo update; updated feed update logic to
  check if relative path matches before allowing update (pkilambi@redhat.com)
- updated log config for rhel5, remove spaces from 'handlers'
  (jmatthews@redhat.com)
- Fix to work around http://bugs.python.org/issue3136 in python 2.4
  (jmatthews@redhat.com)
- Pulp logging now uses configuration file from /etc/pulp/logging
  (jmatthews@redhat.com)
- adding new createrepo as a dependency for el5 builds (pkilambi@redhat.com)
- 709514 - error message for failed errata install for consumer and
  consumergroup corrected (skarmark@redhat.com)
- Automatic commit of package [createrepo] minor release [0.9.8-3].
  (pkilambi@redhat.com)
- Adding newer version of createrepo for pulp on el5 (pkilambi@redhat.com)
- Tell systemctl to ignore deps so that our init script works correctly on
  Fedora 15 (jslagle@redhat.com)
- 713183 - python 2.4 compat patch (pkilambi@redhat.com)
-  Patch from Chris St. Pierre <chris.a.st.pierre@gmail.com> :
  (pkilambi@redhat.com)
- 713580 - fixing wrong list.remove in blacklist filter application logic in
  repo sync (skarmark@redhat.com)
- 669520 python 2.4 compat fix (jslagle@redhat.com)
- 713176 - Changed user certificate expirations to 1 week. Consumer certificate
  expirations, while configurable, remain at the default of 10 years.
  (jason.dobies@redhat.com)
- 669520 - handle exception during compilation of invalid regular expression
  so that we can show the user a helpful message (jslagle@redhat.com)

* Tue Jun 21 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.194-1
- Move repos under /var/lib/pulp-cds/repos so we don't serve packages straight
  up (jason.dobies@redhat.com)

* Tue Jun 21 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.193-1
- 707295 - removed relativepath from repo update; updated feed update logic to
  check if relative path matches before allowing update (pkilambi@redhat.com)
- 713493 - fixed auth login to relogin new credentials; will just replace
  existing user certs with new ones (pkilambi@redhat.com)
- Tell grinder to use a single location for package storage.
  (jason.dobies@redhat.com)
- 714691 - fixed type that caused params to resolve to an instance method
  instead of a local variable (jconnor@redhat.com)
- Fixed incorrect variable name (jason.dobies@redhat.com)
- Added CDS sync history to CDS CLI API (jason.dobies@redhat.com)
- Remove unneeded log.error for translate_to_utf8 (jmatthews@redhat.com)
- Added CLI API call for repo sync history (jason.dobies@redhat.com)
- changed corresponding unittest (jconnor@redhat.com)
- changed scheduled task behavior to reset task states on enqueue instead of on
  run (jconnor@redhat.com)
- Changed unit test logfile to /tmp/pulp_unittests.log, avoid log file being
  deleted when unit tests run (jmatthews@redhat.com)
- updated log config for rhel5, remove spaces from 'handlers'
  (jmatthews@redhat.com)
- Disable console logging for unit tests (jmatthews@redhat.com)
- Fix to work around http://bugs.python.org/issue3136 in python 2.4
  (jmatthews@redhat.com)
- Updates for Python 2.4 logging configuration file (jmatthews@redhat.com)
- Pulp logging now uses configuration file from /etc/pulp/logging
  (jmatthews@redhat.com)
- 713176 - Changed user certificate expirations to 1 week. Consumer certificate
  expirations, while configurable, remain at the default of 10 years.
  (jason.dobies@redhat.com)
- more specific documentation (jconnor@redhat.com)
- missed a find_async substitution (jconnor@redhat.com)
- refactored auth_required and error_handler decorators out of JSONController
  base class and into their own module (jconnor@redhat.com)
- eliminated AsyncController class (jconnor@redhat.com)
- making args and kwargs optional (jconnor@redhat.com)
- fixed bug in server class name and added raw request method
  (jconnor@redhat.com)
- default to no debug in web.py (jconnor@redhat.com)
- print the body instead of returning it (jconnor@redhat.com)
- quick and dirty framework for web.py parameter testing (jconnor@redhat.com)
- Updated for CR 13 (jason.dobies@redhat.com)
- Merge branch 'master' of git://git.fedorahosted.org/git/pulp
  (jslagle@redhat.com)
- bz# 709395 Fix cull_history api to convert to iso8601 format
  (jslagle@redhat.com)
- bz# 709395 Update tests for consumer history events to populate test data in
  iso8601 format (jslagle@redhat.com)
- Merge branch 'master' of git://git.fedorahosted.org/git/pulp
  (jslagle@redhat.com)
- bz# 709395 Fix bug in parsing of start_date/end_date when querying for
  consumer history (jslagle@redhat.com)

 Jun 17 2011 Jeff Ortel <jortel@redhat.com> 0.0.192-1
- 713493 - fixed auth login to relogin new credentials; will just replace
  existing user certs with new ones (pkilambi@redhat.com)
- Bump website to CR13. (jortel@redhat.com)
- Automatic commit of package [pulp] release [0.0.191-1]. (jortel@redhat.com)
- Changed unit test logfile to /tmp/pulp_unittests.log, avoid log file being
  deleted when unit tests run (jmatthews@redhat.com)
- Adding mongo 1.7.5 as a requires for f15 pulp build (pkilambi@redhat.com)
- 707295 - removed relativepath from repo update; updated feed update logic to
  check if relative path matches before allowing update (pkilambi@redhat.com)
- In a consumer case, password can be none, let it return the user
  (pkilambi@redhat.com)
- updated log config for rhel5, remove spaces from 'handlers'
  (jmatthews@redhat.com)
- Disable console logging for unit tests (jmatthews@redhat.com)
- Fix to work around http://bugs.python.org/issue3136 in python 2.4
  (jmatthews@redhat.com)
- Updates for Python 2.4 logging configuration file (jmatthews@redhat.com)
- Pulp logging now uses configuration file from /etc/pulp/logging
  (jmatthews@redhat.com)
- adding new createrepo as a dependency for el5 builds (pkilambi@redhat.com)
- 709514 - error message for failed errata install for consumer and
  consumergroup corrected (skarmark@redhat.com)
- Automatic commit of package [createrepo] minor release [0.9.8-3].
  (pkilambi@redhat.com)
- Adding newer version of createrepo for pulp on el5 (pkilambi@redhat.com)
- Tell systemctl to ignore deps so that our init script works correctly on
  Fedora 15 (jslagle@redhat.com)
- 713183 - python 2.4 compat patch (pkilambi@redhat.com)
- Patch from Chris St. Pierre <chris.a.st.pierre@gmail.com> :
  (pkilambi@redhat.com)
- 713580 - fixing wrong list.remove in blacklist filter application logic in
  repo sync (skarmark@redhat.com)
- 669520 python 2.4 compat fix (jslagle@redhat.com)
- 713176 - Changed user certificate expirations to 1 week. Consumer certificate
  expirations, while configurable, remain at the default of 10 years.
  (jason.dobies@redhat.com)
- 669520 - handle exception during compilation of invalid regular expression
  so that we can show the user a helpful message (jslagle@redhat.com)
- Refactored auth_required and error_handler decorators out of JSONController
  base class and into their own module (jconnor@redhat.com)
- Eliminated AsyncController class (jconnor@redhat.com)
- Fixed bug in server class name and added raw request method
  (jconnor@redhat.com)
- Default to no debug in web.py (jconnor@redhat.com)
- Updated for CR 13 (jason.dobies@redhat.com)
- 709395 - Fix cull_history api to convert to iso8601 format
  (jslagle@redhat.com)
- 709395 - Update tests for consumer history events to populate test data in
  iso8601 format (jslagle@redhat.com)
- 709395 - Fix bug in parsing of start_date/end_date when querying for
  consumer history (jslagle@redhat.com)

* Fri Jun 17 2011 Jeff Ortel <jortel@redhat.com> 0.0.191-1
- Tell systemctl to ignore deps so that our init script works correctly on
  Fedora 15 (jslagle@redhat.com)
- Adding mongo 1.7.5 as a requires for f15 pulp build (pkilambi@redhat.com)

* Mon Jun 13 2011 Jeff Ortel <jortel@redhat.com> 0.0.190-1
- 707295 - updated to provide absolute path. (jortel@redhat.com)
- added tasks module to restapi doc generation (jconnor@redhat.com)
- added wiki docs for tasks collection (jconnor@redhat.com)
- added task history object details (jconnor@redhat.com)
- changing default exposure of tasking command to false (jconnor@redhat.com)
- added sync history to pic (jconnor@redhat.com)
- Disabling part of test_get_repo_packages_multi_repo that is causing test to
  take an excessive amount of time (jmatthews@redhat.com)
- Adding a 3 min timeout for test_get_repo_packages_multi_repo
  (jmatthews@redhat.com)
- 712366 - Canceling a restored sync task does not work (jmatthews@redhat.com)
- 701736 - currently syncing field shows 100% if you run repo status on a
  resync as soon as you run repo sync (jmatthews@redhat.com)
- Renamed group to cluster in CLI output (jason.dobies@redhat.com)
- Enhace incremental feedback to always show progress (pkilambi@redhat.com)
- changed return of delete to task instead of message (jconnor@redhat.com)
- fixed type in delete action (jconnor@redhat.com)
- removed superfluous ?s in regexes (jconnor@redhat.com)
- forgot leading /s (jconnor@redhat.com)
- fixed wrong set call to add elements in buld (jconnor@redhat.com)
- convert all iterable to tuples from task queries (jconnor@redhat.com)
- resolved name collision in query methods and complete callback
  (jconnor@redhat.com)
- changed inheritence to get right methods (jconnor@redhat.com)
- forgot to actually add the command to the script (jconnor@redhat.com)
- tied new task command into client.conf (jconnor@redhat.com)
- tied in new task command (jconnor@redhat.com)
- added task and snapshot formatting and output (jconnor@redhat.com)
- added class_name field to task summary (jconnor@redhat.com)
- first pass at implementing tasks command and associated actions
  (jconnor@redhat.com)
- Need to have the RPM create the cluster files and give them apache ownership;
  if root owns it apache won't be able to chmod them, and this is easier than
  jumping through those hoops. (jason.dobies@redhat.com)
- Trimmed out the old changelog again (jason.dobies@redhat.com)
- add all state and state validation (jconnor@redhat.com)
- added tasks web application (jconnor@redhat.com)
- added snapshot controllers (jconnor@redhat.com)
- added snapshot id to individual task (jconnor@redhat.com)
- changed task delete to remove the task instead of cancel it
  (jconnor@redhat.com)
- start of task admin web services (jconnor@redhat.com)
- added query methods to async and queue (jconnor@redhat.com)

* Fri Jun 10 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.189-1
- removing errata type constraint from help (skarmark@redhat.com)
- 704194 - Add path component of sync URL to event. (jortel@redhat.com)
- Allow for ---PRIVATE KEY----- without (RSA|DSA) (jortel@redhat.com)
- Fix pulp-client consumer bind to pass certificates to repolib.
  (jortel@redhat.com)
- Fix bundle.validate(). (jortel@redhat.com)
- 704599 - rephrase the select help menu (pkilambi@redhat.com)
- Fix global auth for cert consolidation. (jortel@redhat.com)
- 697206 - Added force option to CDS unregister to be able to remove it even if
  the CDS is offline. (jason.dobies@redhat.com)
- changing the epoch to a string; and if an non string is passed force it to be
  a str (pkilambi@redhat.com)
- migrate epoch if previously empty string  and set to int
  (pkilambi@redhat.com)
- Pass certificate PEM instead of paths on bind. (jortel@redhat.com)
- Fix merge weirdness. (jortel@redhat.com)
- Seventeen taken on master. (jortel@redhat.com)
- Adding a verbose option to yum plugin(on by default) (pkilambi@redhat.com)
- Merge branch 'master' into key-cert-consolidation (jortel@redhat.com)
- Migration chnages to convert pushcount from string to an integer value of 1
  (pkilambi@redhat.com)
- removing constraint for errata type (skarmark@redhat.com)
- 701830 - race condition fixed by pushing new scheduler assignment into the
  task queue (jconnor@redhat.com)
- removed re-raising of exceptions in task dispatcher thread to keep the
  dispatcher from exiting (jconnor@redhat.com)
- added docstring (jconnor@redhat.com)
- added more information on pickling errors for better debugging
  (jconnor@redhat.com)
- Add nss DB script to playpen. (jortel@redhat.com)
- Go back to making --key optional. (jortel@redhat.com)
- Move Bundle class to common. (jortel@redhat.com)
- Support CA, client key/cert in pulp.repo. (jortel@redhat.com)
- stop referencing feed_key option. (jortel@redhat.com)
- consolidate key/cert for repo auth certs. (jortel@redhat.com)
- consolidate key/cert for login & consumer certs. (jortel@redhat.com)

* Wed Jun 08 2011 Jeff Ortel <jortel@redhat.com> 0.0.188-1
- 709703 - set the right defaults for pushcount and epoch (pkilambi@redhat.com)
- removed callable from pickling in derived tasks that only can have one
  possible method passed in (jconnor@redhat.com)
- removed lock pickling (jconnor@redhat.com)
- added assertion error messages (jconnor@redhat.com)
- Automatic commit of package [PyYAML] minor release [3.09-14].
  (jmatthew@redhat.com)
- import PyYAML for brew (jmatthews@redhat.com)
- added overriden from_snapshot class methods for derived task classes that
  take different contructor arguments for re-constitution (jconnor@redhat.com)
- fixed snapshot id setting (jconnor@redhat.com)
- extra lines in errata list and search outputs and removing errata type
  constraint (skarmark@redhat.com)
- adding failure message for assert in intervalschedule test case
  (skarmark@redhat.com)
- added --orphaned flag for errata search (skarmark@redhat.com)
- re-arranging calls so that db gets cleaned up before async is initialized,
  keeping persisted tasks from being loaded (jconnor@redhat.com)
- fixing repo delete issue because of missing handling for checking whether
  repo sync invoked is completed (skarmark@redhat.com)
- added individual snapshot removal (jconnor@redhat.com)
- simply dropping whole snapshot collection in order to ensure old snapshots
  are deleted (jconnor@redhat.com)
- adding safe batch removal of task snapshots before enqueueing them
  (jconnor@redhat.com)
- added at scheduled task to get persisted (jconnor@redhat.com)
- Updated User Guide to include jconnor ISO8601 updates from wiki
  (tsanders@redhat.com)
- Bump to grinder 102 (jmatthews@redhat.com)
- Adding lock for creating a document's id because rhel5 uuid.uuid4() is not
  threadsafe (jmatthews@redhat.com)
- Adding checks to check status of the request return and raise exception if
  its not a success or redirect. Also have an optional handle_redirects param
  to tell the request to override urls (pkilambi@redhat.com)
- dont persist the scheduled time, let the scheduler figure it back out
  (jconnor@redhat.com)
- 700367 - bug fix + errata enhancement changes + errata search
  (skarmark@redhat.com)
- reverted custom lock pickling (jconnor@redhat.com)
- refactored and re-arranged functionality in snapshot storage
  (jconnor@redhat.com)
- added ignore_complete flag to find (jconnor@redhat.com)
- changed super calls and comments to new storage class name
  (jconnor@redhat.com)
- remove cusomt pickling of lock types (jconnor@redhat.com)
- consolidate hybrid storage into 1 class and moved loading of persisted tasks
  to async initialization (jconnor@redhat.com)
- moved all timedeltas to pickle fields (jconnor@redhat.com)
- removed complete callback from pickle fields (jconnor@redhat.com)
- added additional copy fields for other derived task classes
  (jconnor@redhat.com)
- reverted repo sync task back to individual fields (jconnor@redhat.com)
- fixed bug in snapshot id (jconnor@redhat.com)
- reverting back to individual field storage and pickling (jconnor@redhat.com)
- removing thread from the snapshot (jconnor@redhat.com)
- delete old thread module (jconnor@redhat.com)
- renamed local thread module (jconnor@redhat.com)
- one more try before having to rename local thread module (jconnor@redhat.com)
- change thread import (jconnor@redhat.com)
- changed to natice lock pickling and unpickling (jconnor@redhat.com)
- added custom pickling and unpickling of rlocks (jconnor@redhat.com)
- 681239 - user update and create now have 2 options of providing password,
  through command line or password prompt (skarmark@redhat.com)
- more thorough lock removal (jconnor@redhat.com)
- added return of None on duplicate snapshot (jconnor@redhat.com)
- added get and set state magic methods to PulpCollection for pickline
  (jconnor@redhat.com)
- using immediate only hybrid storage (jconnor@redhat.com)
- removed cached connections to handle AutoReconnect exceptions
  (jconnor@redhat.com)
- db version 16 for dropping all tasks serialzed in the old format
  (jconnor@redhat.com)
- more cleanup and control flow issues (jconnor@redhat.com)
- removed unused exception type (jconnor@redhat.com)
- fixed bad return on too many consecutive failures (jconnor@redhat.com)
- corrected control flow for exception paths through task execution
  (jconnor@redhat.com)
- using immutable default values for keyword arguments in constructor
  (jconnor@redhat.com)
- added timeout() method to base class and deprecation warnings for usage of
  dangerous exception injection (jconnor@redhat.com)
- removed pickling of individual fields and instead pickle the whole task
  (jconnor@redhat.com)
- comment additions and cleanup (jconnor@redhat.com)
- remove unused persistent storage (jconnor@redhat.com)
- removed unused code (jconnor@redhat.com)
- change in delimiter comments (jconnor@redhat.com)
- adding hybrid storage class that only takes snapshots of tasks with an
  immediate scheduler (jconnor@redhat.com)
- Adding progress call back to get incremental feedback on discovery
  (pkilambi@redhat.com)
- Need apache to be able to update this file as well as root.
  (jason.dobies@redhat.com)
- Adding authenticated repo support to client discovery (pkilambi@redhat.com)
- 704320 - Capitalize the first letter of state for consistency
  (jason.dobies@redhat.com)
- Return a 404 for the member list if the CDS is not part of a cluster
  (jason.dobies@redhat.com)
- Don't care about client certificates for mirror list
  (jason.dobies@redhat.com)
* Sat Jun 04 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.187-1
- Don't need the ping file, the load balancer now supports a members option
  that will be used instead. (jason.dobies@redhat.com)
- Added ability to query just the members of the load balancer, without causing
  the balancing algorithm to take place or the URL generation to be returned.
  (jason.dobies@redhat.com)
- added safe flag to snapshot removal as re-enqueue of a quickly completing,
  but scheduled task can overlap the insertion of the new snapshot and the
  removal of the old without it (jconnor@redhat.com)
- Add 'id' to debug output (jmatthews@redhat.com)
- Fix log statement (jmatthews@redhat.com)
- Adding more info so we can debug a rhel5 intermittent unit test failure
  (jmatthews@redhat.com)
- Automatic commit of package [python-isodate] minor release [0.4.4-2].
  (jmatthew@redhat.com)
- Revert "Fixing test_sync_multiple_repos to use same logic as in the code to
  check running sync for a repo before deleting it" (jmatthews@redhat.com)
- Bug 710455 - Grinder cannot sync a Pulp protected repo (jmatthews@redhat.com)
- Removing unneeded log statements (jmatthews@redhat.com)
- Removed comment (jmatthews@redhat.com)
- Adding ping page (this may change, but want to get this in place now for
  RHUI)) (jason.dobies@redhat.com)
- Enhancements to Discovery Module: (pkilambi@redhat.com)
- Reload CDS before these calls so saved info isn't wiped out
  (jason.dobies@redhat.com)
- Added better check for running syncsI swear I fixed this once...
  (jconnor@redhat.com)
- adding more information to conclicting operation exception
  (jconnor@redhat.com)
- added tear-down to for persistence to unittests (jconnor@redhat.com)
- typo fix (jconnor@redhat.com)
- Revert "renamed _sync to sycn as it is now a public part of the api"
  (jconnor@redhat.com)
- web service for cds task history (jconnor@redhat.com)
- web service for repository task history (jconnor@redhat.com)
- removed old unittests (jconnor@redhat.com)
- new task history api module (jconnor@redhat.com)
- Changed default file name handling so they can be changed in test cases.
  (jason.dobies@redhat.com)
- Refactored CDS "groups" to "cluster". (jason.dobies@redhat.com)
- updating repo file associations (pkilambi@redhat.com)
- update file delete to use new location (pkilambi@redhat.com)
- 709318 - Changing the file store path to be more unique (pkilambi@redhat.com)
