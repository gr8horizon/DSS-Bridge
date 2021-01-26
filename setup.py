# run python3 setup.py py2app

from setuptools import setup

APP = ['DSS_Bridge.py']
DATA_FILES = ['Audium_Logo_Question.png','Audium_Logo.png']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'Audium_Logo.icns',
    'plist': {
        'CFBundleShortVersionString': '0.2.0',
        'LSUIElement': True,
    },
    'packages': ['rumps'],
}

setup(
    app=APP,
    name='DSS Bridge',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'], install_requires=['rumps'], 
)