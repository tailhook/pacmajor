Version 0.1
-----------

* opening other files (patches, etc...)
* implement result checking of some commands
* syncing gits
* colorize menu help
* count files correcly (no dirs)
* handle build errors gracefully
* display merge oportunities in pkgbuild menu
* check file status using git rather comparing with diff
* handle dependency changes during pkgbuild menu correctly
* switch between git/no-git packages
* produce a python package based on distutils info
* handle configuration files in git
* add git log observation in pkgbuild menu

Version 0.2
-----------

* helpers to quickly derive package:
    * py2 <-> py3
    * apply patch
    * edit source and create a patch
    * switch git/svn/hg branch
* better upgrade of patched packages
* .so dependency tracking
* .py dependency tracking (not sure)

Stage 3
-------

* serializable ast of PKGBUILD
* comparison and patch based on ast
