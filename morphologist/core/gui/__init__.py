from __future__ import absolute_import
import os
import sys
# XXX The qt_backend must be imported before any other qt imports (ie. anatomist)
from . import qt_backend
# XXX The ressources must be imported to load icons
if qt_backend.qt_backend.get_qt_backend() == 'PyQt5':
    from . import ressources_qt5 as ressources
elif sys.version_info[0] >= 3:
    from . import ressources_py3 as ressources
from . import ressources

prefix = os.path.dirname(__file__)
ui_directory = os.path.join(prefix, 'ui')