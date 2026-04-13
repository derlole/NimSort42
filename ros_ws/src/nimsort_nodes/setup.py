from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'nimsort_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='benji',
    maintainer_email='wirhassenapple@gmail.com',
    description='Nodes in NimSort Projct',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'nimsort_axis_controller = nimsort_nodes.axis_controller_node:main',
            'nimsort_position_prediction = nimsort_nodes.postion_prediction_node:main',
            'nimsort_vision = nimsort_nodes.camera_supreme_commander:main',
            'nimsort_main = nimsort_nodes.main_node:main'
        ],
    },
)
