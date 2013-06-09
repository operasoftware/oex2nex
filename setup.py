from setuptools import setup

setup(
    name="oex2nex",
    version="0.2.1",
    zip_safe=False,
    packages=["oex2nex"],
    install_requires=("slimit >= 0.8.0", "html5lib"),
    package_data = {
        "oex2nex": ["oex_shim/*"],
    }
)
