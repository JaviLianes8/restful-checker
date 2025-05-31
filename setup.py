from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='restful-checker',
    version='0.1.32',
    description='Check RESTful API compliance from OpenAPI definitions and generate HTML reports',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Javier Lianes García',
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
    project_urls={
        "GitHub": "https://github.com/JaviLianes8/restful-checker",
        "LinkedIn": "https://www.linkedin.com/in/jlianes/"
    },
)