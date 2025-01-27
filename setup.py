from setuptools import setup, find_packages

setup(
    name='ai4ensic',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'python-dotenv==1.0.1',
        'termcolor==2.4.0',
        'chardet==5.2.0',
        'pydantic==2.9.2',
        'ipykernel==6.29.5',
        'openai==1.51.0',
        'instructor==1.5.0',
        'bs4==0.0.2',
        'requests==2.32.3',
        'scapy',
        'pyshark'
    ],
    include_package_data=True,
)
