Pacmajor
========

Pacmajor is an Archlinux package manager. Precisely it's pacman
frontend, with extra functionality for working with AUR.

Basic features:

* keeping track of PKGBUILD history using git
* have separate branch for history in aur and local changes
* have simple utility for patching PKGBUILDs (bump version/release,
  merges, more to come)
* allows to edit all PKGBUILDs at once (comparing to yaourt)
* automatically adds built packages to local repository

Usage
-----

Currently pacmajor supports only install action, and this is also
default one. Usage::

    pacmajor PKGNAME [PKGNAME...]
