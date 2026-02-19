from __future__ import annotations

from setuptools import Extension, find_packages, setup

from Cython.Build import cythonize


extensions = [
    Extension(
        "dig_worker.native.metrics",
        ["dig_worker/native/metrics.pyx"],
    )
]

setup(
    name="dig-ai-worker",
    version="0.1.0",
    description="DIG OS useful-compute worker",
    packages=find_packages(),
    ext_modules=cythonize(extensions, language_level=3),
    zip_safe=False,
)

