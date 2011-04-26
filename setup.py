from distutils.core import setup

setup(name='pacmajor',
    version='0.1',
    description='Package manager for Arch Linux (pacman frontend)',
    author='Paul Colomiets',
    author_email='pc@gafol.net',
    url='http://github.com/tailhook/pacmajor',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        ],
    packages=['pacmajor'],
    package_data={'pacmajor': ['pacmajor.conf']},
    scripts=['scripts/major'],
    requires=['pyarchive'],
    )
