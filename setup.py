from setuptools import find_packages, setup

with open("app/README.md", "r") as f:
    long_description = f.read()

setup(
    name="carbontracking",
    version="0.0.11",
    description="A carbon tracking library for Python applications",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    package_data={'': ['templates/index.html', 'static/assets/bootstrap/css/*', 'static/assets/bootstrap/js/*', 'static/assets/fonts/*', 'static/assets/img/*', 'static/assets/js/*']},
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    author="Peter Rolfes",
    author_email="pero01@dfki.de",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'codecarbon',
        'requests',
        'numpy',
        'pandas',
        'psutil',
        'rapidfuzz',
        'flask',
        'flask_sqlalchemy',
        'sqlalchemy',
        'statistics',
        'collection',
        'thread',
        'jsons',
        'codecarbon',
        'entsoe-py',
    ],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    python_requires=">=3.10",
)