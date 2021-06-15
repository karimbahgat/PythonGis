try: from setuptools import setup
except: from distutils.core import setup

setup(	long_description=open("README.rst").read(), 
	long_description_content_type="text/x-rst",
	name="""PythonGIS""",
	license="""MIT""",
	author="""Karim Bahgat""",
	author_email="""karim.bahgat.norway@gmail.com""",
	url="""http://github.com/karimbahgat/PythonGIS""",
	package_data={'pythongis': ['app/(old)/logo.ico', 'app/(old)/icons/add_layer.png', 'app/(old)/icons/buffer.png', 'app/(old)/icons/clean.png', 'app/(old)/icons/data_options.png', 'app/(old)/icons/delete_layer.png', 'app/(old)/icons/layers.png', 'app/(old)/icons/mosaic.png', 'app/(old)/icons/overlap.png', 'app/(old)/icons/properties.png', 'app/(old)/icons/rename.png', 'app/(old)/icons/resample.png', 'app/(old)/icons/save.png', 'app/(old)/icons/save_image.png', 'app/(old)/icons/split.png', 'app/(old)/icons/vector_merge.png', 'app/(old)/icons/zonalstats.png', 'app/(old)/icons/zoom_global.png', 'app/(old)/icons/zoom_rect.png', 'app/icons/3d icon.png', 'app/icons/accept.png', 'app/icons/arrow_left.png', 'app/icons/arrow_right.png', 'app/icons/axes.png', 'app/icons/config.png', 'app/icons/config2.png', 'app/icons/delete.png', 'app/icons/draw.png', 'app/icons/flatmap.jfif', 'app/icons/identify.png', 'app/icons/layers.png', 'app/icons/measure.png', 'app/icons/minus.ico', 'app/icons/perspectivemap.jpg', 'app/icons/plus.png', 'app/icons/projections.png', 'app/icons/save.png', 'app/icons/zoom_global.png', 'app/icons/zoom_rect.png', 'app/tk2/VISION.md', 'app/tk2/filednd/Linux/libtkdnd2.8.so', 'app/tk2/filednd/Linux/pkgIndex.tcl', 'app/tk2/filednd/Linux/tkdnd.tcl', 'app/tk2/filednd/Linux/tkdnd_compat.tcl', 'app/tk2/filednd/Linux/tkdnd_generic.tcl', 'app/tk2/filednd/Linux/tkdnd_macosx.tcl', 'app/tk2/filednd/Linux/tkdnd_unix.tcl', 'app/tk2/filednd/Linux/tkdnd_windows.tcl', 'app/tk2/filednd/OSX/libtkdnd2.8.dylib', 'app/tk2/filednd/OSX/pkgIndex.tcl', 'app/tk2/filednd/OSX/tkdnd.tcl', 'app/tk2/filednd/OSX/tkdnd_compat.tcl', 'app/tk2/filednd/OSX/tkdnd_generic.tcl', 'app/tk2/filednd/OSX/tkdnd_macosx.tcl', 'app/tk2/filednd/OSX/tkdnd_unix.tcl', 'app/tk2/filednd/OSX/tkdnd_windows.tcl', 'app/tk2/filednd/Windows/32/libtkdnd2.8.dll', 'app/tk2/filednd/Windows/32/pkgIndex.tcl', 'app/tk2/filednd/Windows/32/tkdnd.tcl', 'app/tk2/filednd/Windows/32/tkdnd_compat.tcl', 'app/tk2/filednd/Windows/32/tkdnd_generic.tcl', 'app/tk2/filednd/Windows/32/tkdnd_macosx.tcl', 'app/tk2/filednd/Windows/32/tkdnd_unix.tcl', 'app/tk2/filednd/Windows/32/tkdnd_windows.tcl', 'app/tk2/filednd/Windows/64/pkgIndex.tcl', 'app/tk2/filednd/Windows/64/tkdnd.tcl', 'app/tk2/filednd/Windows/64/tkdnd28.dll', 'app/tk2/filednd/Windows/64/tkdnd_compat.tcl', 'app/tk2/filednd/Windows/64/tkdnd_generic.tcl', 'app/tk2/filednd/Windows/64/tkdnd_macosx.tcl', 'app/tk2/filednd/Windows/64/tkdnd_unix.tcl', 'app/tk2/filednd/Windows/64/tkdnd_windows.tcl', 'app/tk2/_othermisc/dropdown.gif']},
	version="""0.3.0""",
	keywords="""GIS spatial read write management conversion analysis distances visualization""",
	packages=['pythongis', 'pythongis/app', 'pythongis/app/(old)', 'pythongis/app/(old)/icons', 'pythongis/app/(old)/toolkit', 'pythongis/app/icons', 'pythongis/app/tk2', 'pythongis/app/tk2/filednd', 'pythongis/classypie', 'pythongis/raster', 'pythongis/vector', 'pythongis/vector/fileformats', 'pythongis/vector/fileformats/thirdparty', 'pythongis/vector/fileformats/thirdparty/PyDTA', 'pythongis/vector/fileformats/thirdparty/stata_dta', 'pythongis/vector/fileformats/thirdparty/stata_dta/stata_math', 'pythongis/vector/fileformats/thirdparty/stata_dta/stata_missing'],
	install_requires=['shapely', 'pyproj', 'pycrs', 'pyshp', 'pygeoj', 
					'geographiclib', 'pyqtree', 'Pillow', 'colour', 
					'xlrd', 'xlwt', 'openpyxl',
					'PyAgg @ git+https://github.com/karimbahgat/PyAgg', # just until i can push the py3 fix to pypi
					],
	#dependency_links=['https://github.com/karimbahgat/PyAgg/tarball/master'],
	classifiers=['License :: OSI Approved', 'Programming Language :: Python', 'Development Status :: 4 - Beta', 'Intended Audience :: Developers', 'Intended Audience :: Science/Research', 'Intended Audience :: End Users/Desktop', 'Topic :: Scientific/Engineering :: GIS'],
	description="""A simple Python GIS framework for doing actual work.""",
	)
