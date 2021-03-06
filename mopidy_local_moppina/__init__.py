from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local-Moppina'
    ext_name = 'local-moppina'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        return schema

    def setup(self, registry):
        logger.debug('Install Moppina library...')
        from .library import MoppinaLibrary
        registry.add('local:library', MoppinaLibrary)
        logger.debug('Moppina library installed')
