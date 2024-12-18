%global name    lbnl-nhc
%global version 1.4.3
%global release %{rel}%{?dist}

### Macros to populate RPM %{RELEASE} field with useful info
# {gitrelease} holds the ./configure-generated version of the same
# info that's calculated for {spec_rel} below.  This allows us to
# build out-of-tree with the same Git info.
%global gitrelease 1.0.gd534
# {gd_rel_delta} uses "git describe" to return a string in the form
# "<commits>.g<hash>[.1]?" to be used in {spec_rel} below.
%{expand:%%global gd_rel_delta %(GD1=`git describe --abbrev=4 --always --tags --long --match '[[:digit:]][[:alnum:].]*[[:alnum:]]' --dirty=.1 2>/dev/null` ; test -n "${GD1}" && echo "${GD1}" | cut -d- -f 2- | tr '-' '.')%%{nil}}
# {rel_pre_post} gets set to either "1." or "0." based on whether the
# source was built from a commit before ("0.") or after ("1.") the
# tagged release specified by {version} above.
%{expand:%%global rel_pre_post %(GD2=`git describe --tags HEAD 2>/dev/null` ; if test -n "${GD2}" ; then echo "${GD2}" | grep -Eq '^%{version}' >&/dev/null && echo 1. || echo 0. ; fi)%%{nil}}
# {spec_rel} combines the two values above into a single string for
# use in the "Release:" field.  The resulting string, when used at the
# beginning of the "Release:" header value, not only guarantees
# correct RPM NEVR ordering (i.e., newer packages will always upgrade
# older ones) but also shows how many <commits> were made since the
# last tagged release, the Git commit <hash> from which the source
# tarball ("Source:" below) was built, and whether the tarball also
# contains some uncommitted changes from a "dirty" working tree (".1"
# on the end).
%{expand:%%global spec_rel %{?rel_pre_post}%{?gd_rel_delta}%%{nil}}
# {rel} ultimately determines what the release string will be; only
# the disttag gets appended to it.  If the user specifies their own
# value (e.g., "rpmbuild --define 'rel 1'"), that value is used
# instead.  If not, the string described above is pulled either from
# {spec_rel} (if building from Git repo) or {gitrelease} (if building
# from SRPM or source tarball).
# As a special case, if the commit being built exactly matches the Git
# tag for the specified version, {rel} is set to either "1" (clean
# working directory) or "1.1" (dirty working directory).
%{!?rel:%{expand:%%global rel %(REL="%{?spec_rel}%{!?spec_rel:%{gitrelease}}" ; if (echo "${REL:-nope}" | grep -Fq "1.0.g" 2>/dev/null) ; then if (echo "${REL:-nope}" | grep -q '\.1$' 2>/dev/null) ; then echo "1.1" ; else echo 1 ; fi ; elif test -z "%{spec_rel}" ; then echo "%{gitrelease}" ; else echo "%{spec_rel}" ; fi)%{nil}}}

%{!?sname:%global sname nhc}
%{!?nhc_script_dir:%global nhc_script_dir %{_sysconfdir}/%{sname}/scripts}
%{!?nhc_helper_dir:%global nhc_helper_dir %{_libexecdir}/%{sname}}


Summary: LBNL Node Health Check
Name: %{name}
Version: %{version}
Release: %{release}
#Release: 1%{?dist}
# LBNL Open Source License:  https://opensource.org/BSD-3-Clause-LBNL
License: BSD-3-Clause-LBNL
Group: Applications/System
URL: https://github.com/mej/nhc/
Source: https://github.com/mej/nhc/archive/%{name}-%{version}.tar.gz
Packager: %{?_packager}%{!?_packager:Michael Jennings <mej@eterm.org>}
Vendor: %{?_vendorinfo}%{!?_vendorinfo:LBNL NHC Project (https://github.com/mej/nhc/)}
Requires: bash
Obsoletes: warewulf-nhc <= 1.4.2-1
BuildArch: noarch
BuildRoot: %{?_tmppath}%{!?_tmppath:/var/tmp}/%{name}-%{version}-%{release}-root

%description
This package contains the LBNL Node Health Check (NHC) system.
Originally written to serve a very specific niche in validating
compute nodes of High-Performance Computing (HPC) clusters, its unique
combination of extensibility, portability, simplicity, and efficiency
have made it a popular general-purpose system health monitoring and
management tool.

Complete documentation and example use cases are available on the
project home page at https://github.com/mej/nhc


%prep
%setup


%build
%{configure}
%{__make} %{?mflags}


%install
umask 0077
%{__make} install DESTDIR=$RPM_BUILD_ROOT %{?mflags_install}


%check
%{__make} test


%triggerpostun -p /bin/bash -- warewulf-nhc <= 1.4.2-1
if [ $1 -gt 0 -a $2 -eq 0 ]; then
    cd %{_sysconfdir}/%{sname}/scripts
    for SCRIPT in ww_*.nhc.rpmsave ; do
        if [ -e $SCRIPT ]; then
            NEWSCRIPT=lbnl${SCRIPT##ww}
            NEWSCRIPT=${NEWSCRIPT%%.rpmsave}
            echo warning: Auto-fixing script naming due to modified script ${SCRIPT%%.rpmsave}
            mv -v $NEWSCRIPT $NEWSCRIPT.rpmnew && mv -v $SCRIPT $NEWSCRIPT
        fi
    done 2>/dev/null
fi


%clean
test "$RPM_BUILD_ROOT" != "/" && %{__rm} -rf $RPM_BUILD_ROOT


%files
%defattr(-, root, root)
%doc COPYING ChangeLog LICENSE nhc.conf contrib/nhc.cron
%dir %{_sysconfdir}/%{sname}/
%dir %{_localstatedir}/lib/%{sname}/
%dir %{_localstatedir}/run/%{sname}/
%dir %{nhc_script_dir}/
%dir %{nhc_helper_dir}/
%ghost %dir %{_sysconfdir}/%{sname}/sysconfig/
%config(noreplace) %{_sysconfdir}/%{sname}/%{sname}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{sname}
%config(noreplace) %{nhc_script_dir}/*.nhc
%config(noreplace) %{nhc_helper_dir}/*
%config(noreplace) %{_sbindir}/%{sname}
%config(noreplace) %{_sbindir}/%{sname}-genconf
%config(noreplace) %{_sbindir}/%{sname}-wrapper
