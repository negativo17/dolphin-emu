%global commit0 637bdc45b388ebd38a59a9496cea474fe3200ab8
%global date 20170403
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

%undefine _hardened_build

Name:           dolphin-emu
Summary:        Dolphin Emulator
Version:        5.0
Release:        14%{?shortcommit0:.%{date}git%{shortcommit0}}%{?dist}
# The project is licensed under GPLv2+ with some notable exceptions
#  Source/Core/Common/GL/GLExtensions/* is MIT
#  Source/Core/Core/HW/Sram.h is zlib
#  Source/Core/Common/GekkoDisassembler.* is BSD (2 clause)
# The following is BSD (3 clause):
#  Source/Core/Common/SDCardUtil.cpp
#  Source/Core/Common/BitField.h
#  Source/Core/Core/IPC_HLE/l2cap.h
#  Source/Core/Core/IPC_HLE/hci.h
#  Source/Core/VideoBackends/Software/Clipper.cpp
#  Source/Core/AudioCommon/aldlist.cpp
# Any code in Externals has a license break down in Externals/licenses.md
License:        GPLv2+ and BSD and MIT and zlib
URL:            https://dolphin-emu.org/
ExclusiveArch:  x86_64 armv7l aarch64

Source0:        https://github.com/dolphin-emu/dolphin/archive/%{commit0}/dolphin-%{commit0}.tar.gz#/%{name}-%{shortcommit0}.tar.gz
Source1:        %{name}.appdata.xml

BuildRequires:  bochs-devel
BuildRequires:  cmake >= 2.8
BuildRequires:  desktop-file-utils
BuildRequires:  enet-devel
BuildRequires:  ffmpeg-devel
BuildRequires:  gcc-c++
BuildRequires:  gettext
# Required only with a git clone
# BuildRequires:  git
BuildRequires:  glibc-headers
BuildRequires:  gtest-devel
BuildRequires:  gtk3-devel
BuildRequires:  hidapi-devel
BuildRequires:  libappstream-glib
BuildRequires:  libcurl-devel
BuildRequires:  libevdev-devel
BuildRequires:  libSM-devel
BuildRequires:  libusb-devel
BuildRequires:  libusb-devel
BuildRequires:  lzo-devel
BuildRequires:  mbedtls-devel
BuildRequires:  miniupnpc-devel
BuildRequires:  openal-soft-devel
BuildRequires:  pkgconfig(alsa)
BuildRequires:  pkgconfig(ao)
BuildRequires:  pkgconfig(bluez)
BuildRequires:  pkgconfig(libpulse)
BuildRequires:  pkgconfig(xrandr)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  portaudio-devel
BuildRequires:  SDL2-devel
BuildRequires:  SFML-devel
BuildRequires:  SOIL-devel
BuildRequires:  soundtouch-devel
BuildRequires:  systemd-devel
BuildRequires:  vulkan-devel
# Requires minimum version 3.1.0, not yet in Fedora
# BuildRequires:  wxGTK3-devel

Requires:       %{name}-data = %{?epoch}:%{version}-%{release}
Requires:       hicolor-icon-theme
Requires:       perl(Net::DBus)
Requires:       perl(X11::Protocol)

# xxhash is bundled for now, will be unbundled after included in Fedora:
# https://bugzilla.redhat.com/show_bug.cgi?id=1282063
# Note that xxhash was unversioned prior to 0.5.0, 0.4.39 is a placeholder
# It was actually called r39: https://github.com/Cyan4973/xxHash/tree/r39
Provides:       bundled(xxhash) = 0.4.39

%description
Dolphin is an emulator for two recent Nintendo video game consoles: the GameCube
and the Wii. It allows PC gamers to enjoy games for these two consoles in full
HD (1080p) with several enhancements: compatibility with all PC controllers,
turbo speed, networked multiplayer, and even more!

%package data
Summary:        Dolphin Emulator data files
BuildArch:      noarch

%description data
Common files for Dolphin Emulator packages.

%package nogui
Summary:        Dolphin Emulator without a graphical user interface

%description nogui
Dolphin Emulator without a graphical user interface.

%prep
%setup -qn dolphin-%{commit0}

# Font license, just making things more generic
sed -i -e 's| this directory | %{name}/Sys/GC |g' Data/Sys/GC/font-licenses.txt 
cp Data/Sys/GC/font-licenses.txt .

# Remove Bundled Libraries except xxhash, mentioned above:
cd Externals
rm -rf `ls | grep -E -v 'Bochs|xxhash|glslang|cpp-optparse|wxWidgets3'`

# Remove Bundled Bochs source and replace with links:
cd Bochs_disasm
rm -rf `ls | grep -E -v 'stdafx|CMakeLists.txt'`
ln -s %{_includedir}/bochs/config.h ./config.h
ln -s %{_includedir}/bochs/disasm/* ./

%build
mkdir build
pushd build
%cmake %{?_cmake_skip_rpath} \
    -DDISTRIBUTOR=Fedora \
    -DENABLE_LTO=True \
    -DUSE_SHARED_ENET=True \
    -DUSE_SHARED_GTEST=True \
    ..
make %{?_smp_mflags}
popd

%install
pushd build
%make_install
# udev rules for DolphinBar and GameCube Controller USB adapter
install -m 644 -p -D ../Data/51-usb-device.rules %{buildroot}%{_udevrulesdir}/51-usb-device.rules
popd

%find_lang %{name}

%if 0%{?fedora} >= 25
# Install AppData
mkdir -p %{buildroot}%{_datadir}/appdata/
install -p -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/appdata/
%endif

# rpmlint fixes
find . -name "*.cpp" -exec chmod 644 {} \;
find . -name "*.h" -exec chmod 644 {} \;
find . -name "*.hpp" -exec chmod 644 {} \;

%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/appdata/%{name}.appdata.xml

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files data
%license license.txt font-licenses.txt
%doc Readme.md Contributing.md docs/gc-font-tool.cpp
# For the gui package:
%exclude %{_datadir}/%{name}/sys/Resources/
%exclude %{_datadir}/%{name}/sys/Themes/
%{_datadir}/%{name}
%{_udevrulesdir}/*

%files -f %{name}.lang
%{_bindir}/%{name}
%if 0%{?fedora} >= 25
%{_datadir}/appdata/%{name}.appdata.xml
%endif
%{_datadir}/applications/%{name}.desktop
%{_datadir}/%{name}/sys/Resources/
%{_datadir}/%{name}/sys/Themes/
%{_datadir}/icons/hicolor/48x48/apps/%{name}.*
%{_datadir}/icons/hicolor/scalable/apps/%{name}.*
%{_mandir}/man6/%{name}.*

%files nogui
%{_bindir}/%{name}-nogui
%{_mandir}/man6/%{name}-nogui.*

%changelog
* Tue Apr 04 2017 Simone Caronni <negativo17@gmail.com> - 5.0-14.20170403git637bdc4
- Update files section.

* Mon Apr 03 2017 Simone Caronni <negativo17@gmail.com> - 5.0-13.20170403git637bdc4
- Quick build of a snapshot, adjust spec file.

* Wed Feb 15 2017 Jeremy Newton <alexjnewt at hotmail dot com> - 5.0-12
- Rebuilt SFML 2.4
