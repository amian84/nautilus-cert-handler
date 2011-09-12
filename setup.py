from distutils.core import setup
from DistUtilsExtra.command import *

setup(name='nautilus-cert-handler',
 version='0.1',
    author='David Amian',
    author_email='damian@emergya.com',
    data_files=[('share/nautilus-python/extensions',['scripts/nautilus-cert-handler.py']),
                ('/var/lib/update-notifier/user.d',['data/nautilus-cert-handler-notification'])]
    cmdclass = { "build" : build_extra.build_extra,
        "build_i18n" :  build_i18n.build_i18n,
        "clean": clean_i18n.clean_i18n, 
        }
    )
