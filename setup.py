import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-email-verification",
    version="0.3.0.rc2",
    author="Leone Bacciu",
    author_email="leonebacciu@gmail.com",
    description="Email confirmation app for django",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeoneBacciu/django-email-verification",
    packages=setuptools.find_packages(exclude=['django_email_verification.tests']),
    install_requires=[
        'deprecation',
        'PyJWT'
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
