import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DataAPI",
    version="1.0.0",
    author="Gustavo Curi Amarante",
    description="Macroeconomy time series data acquisition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="www.github.com/gusamarante/FinaceLab",
    packages=setuptools.find_packages(),
    install_requires=['pandas'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Macroeconomy :: Time Series",
        "Macroeconomy :: Data Acquisition"
    ),
)
