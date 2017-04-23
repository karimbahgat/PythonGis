try: from setuptools import setup
except: from distutils.core import setup

setup(	long_description=open("README.rst").read(), 
	name="""PythonGIS""",
	license="""MIT""",
	author="""Karim Bahgat""",
	author_email="""karim.bahgat.norway@gmail.com""",
	url="""http://github.com/karimbahgat/PythonGIS""",
	package_data={'pythongis': ['app/(old)/logo.ico', 'app/(old)/icons/add_layer.png', 'app/(old)/icons/buffer.png', 'app/(old)/icons/clean.png', 'app/(old)/icons/data_options.png', 'app/(old)/icons/delete_layer.png', 'app/(old)/icons/layers.png', 'app/(old)/icons/mosaic.png', 'app/(old)/icons/overlap.png', 'app/(old)/icons/properties.png', 'app/(old)/icons/rename.png', 'app/(old)/icons/resample.png', 'app/(old)/icons/save.png', 'app/(old)/icons/save_image.png', 'app/(old)/icons/split.png', 'app/(old)/icons/Thumbs.db', 'app/(old)/icons/vector_merge.png', 'app/(old)/icons/zonalstats.png', 'app/(old)/icons/zoom_global.png', 'app/(old)/icons/zoom_rect.png', 'app/icons/identify.png', 'app/icons/layers.png', 'app/icons/save.png', 'app/icons/Thumbs.db', 'app/icons/zoom_global.png', 'app/icons/zoom_rect.png']},
	version="""0.1.0""",
	keywords="""GIS spatial read write management conversion analysis distances visualization""",
	packages=['pythongis', 'pythongis/app', 'pythongis/app/(old)', 'pythongis/app/(old)/icons', 'pythongis/app/(old)/toolkit', 'pythongis/raster', 'pythongis/vector', 'pythongis/vector/fileformats', 'pythongis/vector/fileformats/thirdparty', 'pythongis/vector/fileformats/thirdparty/PyDTA', 'pythongis/vector/fileformats/thirdparty/stata_dta', 'pythongis/vector/fileformats/thirdparty/stata_dta/stata_math', 'pythongis/vector/fileformats/thirdparty/stata_dta/stata_missing'],
	requires=['shapely', 'pyshp', 'pygeoj', 'rtree', 'PIL==1.1.7', 'pyagg', 'colour', 'classypie', 'tk2'],
	classifiers=['License :: OSI Approved', 'Programming Language :: Python', 'Development Status :: 4 - Beta', 'Intended Audience :: Developers', 'Intended Audience :: Science/Research', 'Intended Audience :: End Users/Desktop', 'Topic :: Scientific/Engineering :: GIS'],
	description="""A simple Python GIS framework for doing actual work.""",
	)
