from setuptools import setup

SHORT_DESC = 'A library for creating flexible network topologies'
LONG_DESC = 'This library helps you test large networks of nodes across physical and simulated links.'

setup(
    name='mesh-networking',
    version='0.0.7',
    description=SHORT_DESC,
    long_description=LONG_DESC,

    url='https://github.com/pirate/mesh-networking',
    author='Nick Sweeting',
    author_email='mesh-networking@sweeting.me',
    license='MIT',

    classifiers=[
        'Topic :: Utilities',
        'Topic :: System :: Networking',

        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='networking routing mesh osi scapy udp tcp iptables irc',

    packages=['mesh'],
    test_suite='mesh.tests',
    install_requires=[],
)
