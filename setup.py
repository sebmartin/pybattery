from setuptools import setup, find_packages

setup(
    name="pybattery",
    version="0.1.0",
    packages=find_packages(where="pybattery"),
    package_dir={"": "pybattery"},
    install_requires=[
        "dbus-python",
        "pyyaml",
        "pyrover @ git+https://github.com/sebmartin/pyrover.git",
    ],
    extras_require={
        "dev": ["ipython", "pytest"],
    }
    python_requires=">=3.8",
)