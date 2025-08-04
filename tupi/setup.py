from setuptools import setup, find_packages

setup(
    name="tupi",
    version="0.1.2",
    packages=find_packages(),
    include_package_data=True,  # Important!
    package_data={
        "tupi": ["alt_ort/*", "irregular/*"],  # Include all files inside alt_ort
    },
    description="A package for Old Tupi (Navarro orthography) language processing",
    author="Kian Sheik",
    author_email="kiansheik3128@gmail.com",
    url="https://github.com/kiansheik/nhe-enga",
    # Add any other relevant metadata or dependencies
)
