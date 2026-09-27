from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rov_ctrl_sys'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='david',
    maintainer_email='smithd22@oregonstate.edu',
    description='The rov control system package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'joy_to_motor = rov_ctrl_sys.joy_to_motor:main',
            'joy_to_motor_unstick = rov_ctrl_sys.joy_to_motor_unstick:main',
            'joy_to_servo = rov_ctrl_sys.joy_to_servo:main',
            'keyboard_to_servo = rov_ctrl_sys.keyboard_to_servo:main',
            'motor_controller = rov_ctrl_sys.motor_controller:main',
            'crab_detect = rov_ctrl_sys.crab_detect:main',
            'window = rov_ctrl_sys.window:main',
#             'calibrate_motors = rov_ctrl_sys.calibrate_motors:main',
        ],
    },
)
