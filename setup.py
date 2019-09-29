import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-email-verification",
    version="0.0.1",
    author="Leone Bacciu",
    author_email="leonebacciu@gmail.com",
    description="Email verificator app for django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeoneBacciu/django-email-verification",
    packages=setuptools.find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
