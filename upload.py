import pipy
 
packpath = "pythongis"
pipy.define_upload(packpath,
                   author="Karim Bahgat",
                   author_email="karim.bahgat.norway@gmail.com",
                   license="MIT",
                   name="PythonGIS",
                   changes=["First setup test."],
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
                   requires=["shapely",
                             "pyshp",
                             "pygeoj",
                             "rtree",
                             "PIL==1.1.7",
                             "pyagg",
                             "colour",
                             "classipy"],
                   )

#pipy.generate_docs(packpath)
#pipy.upload_test(packpath)
#pipy.upload(packpath)

