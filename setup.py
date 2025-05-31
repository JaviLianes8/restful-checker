from setuptools import setup, find_packages

setup(
    name='restful-checker',
    version='0.1.26',
    description='Check RESTful API compliance from OpenAPI definitions and generate HTML reports',
    author='Javi Lianes',
    author_email='jlianesglr@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pyyaml','requests'],
    entry_points={
        'console_scripts': [
            'restful-checker=restful_checker.main:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)