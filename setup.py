from setuptools import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name='mopidy-yamusic',
    version='1.0',
    description='Mopidy extension for playing music from YandexMusic',
    description_file='README.md',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/stffart/mopidy-yamusic',
    author='stffart',
    author_email='stffart@gmail.com',
    license='GPLv3',
    packages=['mopidy_yamusic'],
    package_dir={'mopidy_yamusic':'mopidy_yamusic'},
    package_data={'mopidy_yamusic':['ext.conf']},
    install_requires=['yandex-music<2.0',
                      ],
    entry_points={
        'mopidy.ext': [
            'yamusic = mopidy_yamusic:Extension',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)

