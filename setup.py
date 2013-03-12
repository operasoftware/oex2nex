from setuptools import setup

setup(
    name="oex2crx",
    version="0.1",
    zip_safe=False,
    packages=["oex2crx"],
    install_requires=("slimit", "html5lib"),
    package_data = {
        "oex2crx": ["oex_shim/*"],
    }
)
