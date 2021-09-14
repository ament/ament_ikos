from setuptools import setup

package_name = 'ament_ikos'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Steven! Ragnarök',
    maintainer_email='steven@openrobotics.org',
    description='ament_lint wrapper around IKOS static analysis utility.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ament_ikos = ament_ikos.main:main',
        ],
    },
)
