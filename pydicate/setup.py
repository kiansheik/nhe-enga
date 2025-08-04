from setuptools import setup, find_packages

setup(
    name="pydicate",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,  # Important!
    package_data={
        # "pydicate": ["../tupi/*",],  # Include all files inside alt_ort
        'pydicate.lang.tupilang': ['data/*.gz'],
    },
    description="A package for generic linguistics processing",
    author="Kian Sheik",
    author_email="kiansheik3128@gmail.com",
    url="https://github.com/kiansheik/nhe-enga",
    # Add any other relevant metadata or dependencies
)
