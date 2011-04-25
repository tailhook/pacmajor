from distutils.core import setup

setup(name='buyore',
    version='0.1',
    description='Package manager for Arch Linux (pacman frontend)',
    author='Paul Colomiets',
    author_email='pc@gafol.net',
    url='http://github.com/tailhook/buyore',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        ],
    packages=['buyore'],
    package_data=['buyore.conf'],
    scripts=['scripts/buy'],
    requires=['pyarchive'],
    )
