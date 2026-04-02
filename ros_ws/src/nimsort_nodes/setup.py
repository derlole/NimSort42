from setuptools import find_packages, setup

package_name = 'nimsort_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
            'nimsort_axis_controller = nimsort_nodes.axis_controller_node:main'
        ],
    },
)
