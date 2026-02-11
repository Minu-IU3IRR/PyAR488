from setuptools import setup, find_packages

project_name = "PyAR488"

def read_version():
    ns = {}
    with open("PyAR488/_version.py", "r", encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns["__version__"]

setup(
    name=project_name,
    version=read_version(),
    packages=find_packages(),
    url="https://github.com/Minu-IU3IRR/PyAR488",
    project_urls={
        "Bug Tracker": "https://github.com/Minu-IU3IRR/PyAR488/issues",
        "Source": "https://github.com/Minu-IU3IRR/PyAR488",
    },
    license="MIT",
    author="Manuel Minutello",
    description="module to interface AR488 boards",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=["pyserial"],
    python_requires=">=3.6",
)
