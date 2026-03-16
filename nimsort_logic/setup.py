from setuptools import setup, find_packages

setup(
    name='nimsort_logic',
    version='0.42.0',
    packages=find_packages(),      # findet automatisch alles im Ordner
    install_requires=[
        # hier deine Python-Abhängigkeiten eintragen, z.B. numpy, requests
    ],
    author='NimSort Dev-Team',
    description='NimSort Logic Python Package',
    python_requires='>=3.10',
)
