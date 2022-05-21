# sroadex_tiles_generation
Public repository from SROADEX project with the code and example about creating tile images and ground true (mask) for deep learning training process

The python script (generate_tiles_sheet_lines.py) creates the folders in which the orthoimage tessellations are saved as the tessellations of the masks resulting from the rasterization of the vials. The script receives as parameters the file containing the axes (shapefile), the orthoimage (geotiff file), the mapfile (mapserver/mapscript) with the configuration to rasterize the axes and the coordinate system (EPSG code).

The file create_tiles.bat contains an example of use, with the provided example files (0203_axis.shp, orthoimage and mapfile).
