from setuptools import setup

setup(
    name='mopidy-yamusic',
    version='0.9',
    description='Mopidy extension for playing music from YandexMusic',
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

