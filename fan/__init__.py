import os
import sys

path = os.path.dirname(__file__)

# Shopify sdk and required libs
sys.path.insert(1, os.path.join(path, '..', 'lib-submodules', 'shopify_python_api'))
sys.path.insert(1, os.path.join(path, '..', 'lib-submodules', 'six'))
sys.path.insert(1, os.path.join(path, '..', 'lib-submodules', 'pyactiveresource'))

import fan