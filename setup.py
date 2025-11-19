from setuptools import setup, find_packages

setup(
    name="agentics_lundmj",  # Name of your package
    version="1.0.1",
    author="Matthew Lund",  # Replace with your name
    author_email="lundmatthewj@gmail.com",  # Replace with your email
    description="A package for building intelligent agents through OpenAI's API.",
    long_description=open("README.md").read(),  # Ensure you have a README.md file
    long_description_content_type="text/markdown",
    url="https://github.com/lundmj/aiAgents",  # Replace with your repository URL
    packages=find_packages(),  # Automatically find all packages in the directory
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Specify the minimum Python version
    install_requires=[
        "openai>=2.7.1",  # OpenAI package for API interactions
    ],
    include_package_data=True,  # Include non-code files specified in MANIFEST.in
)