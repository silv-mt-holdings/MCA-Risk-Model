from setuptools import setup, find_packages

setup(
    name='mca-risk-model',
    version='1.0.0',
    description='MCA Risk Scoring Model - Bank statement parsing, cash flow analytics, and composite scoring',
    author='Silv MT Holdings',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pandas>=1.5.0',
        'numpy>=1.21.0',
        'openpyxl>=3.0.0',
        'pdfplumber>=0.7.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'mca-score=cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
