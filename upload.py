import pipy
 
packpath = "pythongis"
pipy.define_upload(packpath,
                   author="Karim Bahgat",
                   author_email="karim.bahgat.norway@gmail.com",
                   license="MIT",
                   name="PythonGIS",
                   changes=["Misc addons and fixes.",
                            "Better and more stable app and rendering",
                            "Roughly stable for some time"],
                   description="A simple Python GIS framework for doing actual work.",
                   url="http://github.com/karimbahgat/PythonGIS",
                   keywords="GIS spatial read write management conversion analysis distances visualization",
                   classifiers=["License :: OSI Approved",
                                "Programming Language :: Python",
                                "Development Status :: 4 - Beta",
                                "Intended Audience :: Developers",
                                "Intended Audience :: Science/Research",
                                'Intended Audience :: End Users/Desktop',
                                "Topic :: Scientific/Engineering :: GIS"],
                   requires=['shapely',
                             'pyproj',
                             'pycrs',
                             'pyshp',
                             'pygeoj',
                             'pyqtree',
                             'Pillow',
                             'pyagg',
                             'colour',
                             'xlrd',
                             'xlwt',
                             'openpyxl']
                   )

pipy.generate_docs(packpath)
#pipy.upload_test(packpath)
#pipy.upload(packpath)

