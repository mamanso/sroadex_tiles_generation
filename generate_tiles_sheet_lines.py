from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo import gdalconst
import mapscript
import getopt, sys
import os, shutil
import time, glob, math

gdal_env = os.environ.copy()
# Set enviromental variables about GDAL to use OGR Coordinate transformations
#gdal_env["GDAL_DATA"] = '\\miniconda3\\envs\\mapscript2\\Library\\share'
#gdal_env['PROJ_LIB'] = '\\miniconda3\\envs\\mapscript2\\Library\\share\\proj'

# Default output folder name
imgsFolder = 'tiles'

# Read script arguments
argumentList = sys.argv[1:] 
# Short Options 
options = "hf:i:m:d:c:"
# Long options names
long_options = ["Help", "shp_file=", "ortho_image=", "map_file=", "Img_Directory=", "CRS="] 
 
shpFile =''
orthoFile = ''
mapFile = ''
CRS = ''
img_width, img_height = 256, 256

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier
    
if __name__ == '__main__':
    try: 
        # Parsing argument 
        arguments, values = getopt.getopt(argumentList, options, long_options) 
          
        # checking each argument 
        for currentArgument, currentValue in arguments: 
      
            if currentArgument in ("-h", "--Help"): 
                print ("Diplaying Help")
                print ("-f Input image; -ns H5 CNN file name; -nc H5 Cla file name; -d Img_Directory; -c CRS")
                
            elif currentArgument in ("-f", "--shp_file"): 
                print ("Input Image file_name (% s)" % (currentValue))
                shpFile = currentValue
                  
            elif currentArgument in ("-i", "--ortho_image"): 
                print (("Tif ortho image (% s)") % (currentValue))
                orthoFile = currentValue
            elif currentArgument in ("-m", "--map_file"): 
                print (("Mapfile (% s)") % (currentValue))
                mapFile = currentValue                              
            elif currentArgument in ("-d", "--Img_Directory"): 
                print (("Img Directory (% s)") % (currentValue))
                imgsFolder = currentValue
                
            elif currentArgument in ("-c", "--CRS"): 
                print (("Img CRS (% s)") % (currentValue))
                CRS = currentValue             
                
    except getopt.error as err: 
        # output error, and return with an error code 
        print (str(err))

    if not shpFile or not orthoFile or not CRS or not mapFile: 
        sys.exit("There are Not enought input arguments: Input Shp, Ortho image file, MapFile and CRS")

    names = []
    names = glob.glob( orthoFile )


    fName = names[0]
    hojaN = fName[0: 4]

    print("Procesing sheet: %s" % (hojaN))


    # Abrimos el ECW para leer la extensión, dimensiones y poder ir extrayendo tiles de imagen a la par que se generen con MapScript la imagen de la cartografía y se coloquen en carpetas distintas
    
    try:
        from osgeo import gdal
        gdal.TermProgress = gdal.TermProgress_nocb
    except ImportError:
        import gdal



    imgPathroot = os.getcwd() + '/' + imgsFolder + '_' + str(img_width)
    if not os.path.isdir(imgPathroot):
        os.makedirs(imgPathroot)
    imgPathyesortho = os.getcwd() + '/' + imgsFolder + '_' + str(img_width) + '/ok-ortho'
    if not os.path.isdir(imgPathyesortho):
        os.makedirs(imgPathyesortho)
    imgPathyeswms = os.getcwd() + '/' + imgsFolder + '_' + str(img_width) + '/ok-wms'
    if not os.path.isdir(imgPathyeswms):
        os.makedirs(imgPathyeswms)
    imgPathnoortho = os.getcwd() + '/' + imgsFolder + '_' + str(img_width) + '/no-ortho'
    if not os.path.isdir(imgPathnoortho):
        os.makedirs(imgPathnoortho)
    imgPathnowms = os.getcwd() + '/' + imgsFolder + '_' + str(img_width) + '/no-wms'
    if not os.path.isdir(imgPathnowms):
        os.makedirs(imgPathnowms)        
    # image file names patter    
    fN_pattern_yesOrtho = imgPathyesortho + '/' + hojaN + '-{}-{}.png'        
    fN_pattern_yesWMS = imgPathyeswms + '/' + hojaN + '-{}-{}.png' 
    fN_pattern_noOrtho = imgPathnoortho + '/' + hojaN + '-{}-{}.png' 
    fN_pattern_noWMS = imgPathnowms + '/' + hojaN + '-{}-{}.png'    
    
    ds = gdal.Open(orthoFile)
    
    # Read spatial BBOX from raster file
    ancho = ds.RasterXSize
    alto = ds.RasterYSize
    bxmin,resolucion,rot1,bymax,rot2,resy = ds.GetGeoTransform ()
    
    print("Width: ", ancho , " Hight: " , alto , " resolution: ", resolucion)
    bxmax = bxmin + resolucion * ancho
    bymin = bymax - resolucion * alto
    # Establecemos el area de trabajo al máximo que permite la estrategia de 4 img por tile
    bxminarea = bxmin + 128 * resolucion
    byminarea = bymin + 128 * resolucion
    bxmaxarea = bxmax - 128 * resolucion
    bymaxarea = bymax - 128 * resolucion
       
    resolucion2 = resolucion

    filas = int(round_down((bymax - bymin)/(resolucion2 * img_height))) 
    columnas = int(round_down((bxmax - bxmin)/(resolucion2 * img_width))) 

    print("Rows: " , filas, ", Columns: ", columnas)

    filasarea = int(round_down((bymaxarea - byminarea)/(resolucion2 * img_height))) 
    columnasarea = int(round_down((bxmaxarea - bxminarea)/(resolucion2 * img_width)))
   
    print("Area Rows: " , filasarea, ", Area Columns: ", columnasarea)

    start_time = time.time()
    contador = 0
    gdal.TermProgress( 0.0 )

    ds = ogr.Open(shpFile, False)
    lyr = ds.GetLayer() 
    mapscript.msIO_installStdoutToBuffer() # To use MapScript and build images.
    
    req = mapscript.OWSRequest()
    req.setParameter( 'SERVICE', 'WMS' )
    req.setParameter( 'VERSION', '1.1.1' )
    req.setParameter( 'REQUEST', 'GetMap' )
    req.setParameter('STYLES', ',')
    req.setParameter('WIDTH', str(img_width))
    req.setParameter('HEIGHT', str(img_height))
    req.setParameter('SRS', 'EPSG:' + CRS)
    req.setParameter('FORMAT', 'image/png')
    img_length = 0.01 * img_width
    map = mapscript.mapObj( os.getcwd() + '/' + mapFile )

    for i in range(0, filasarea - 1):
        start_timef = time.time()  
        for j in range(0, columnasarea - 1):
            xmin = bxminarea + j * img_width * resolucion2
            xmax = xmin + img_width * resolucion2
            ymax = bymaxarea - i * img_height * resolucion2
            ymin = ymax - img_height * resolucion2
            lyr.SetSpatialFilterRect(xmin, ymin, xmax, ymax )
            SumaLongitudes = 0
            nFeatClipped = 0
            oRing = ogr.Geometry(ogr.wkbLinearRing)
            oRing.AddPoint_2D(xmin, ymin)
            oRing.AddPoint_2D(xmin, ymax)
            oRing.AddPoint_2D(xmax, ymax)
            oRing.AddPoint_2D(xmax, ymin)
            oRing.AddPoint_2D(xmin, ymin)

            poClipSrc = ogr.Geometry(ogr.wkbPolygon)
            poClipSrc.AddGeometry(oRing)
            SumaLongitudes = 0
            nFeatClipped = 0

            for poDstFeature in lyr:
                poDstGeometry = poDstFeature.GetGeometryRef()
                if poDstGeometry :
                    poClipped = poDstGeometry.Intersection(poClipSrc)
                    if poClipped or not poClipped.IsEmpty():
                        SumaLongitudes = SumaLongitudes + poClipped.Length()
                        nFeatClipped = nFeatClipped + 1

          
            req.setParameter('LAYERS','ortho')
            coords = str(xmin) + ", " + str(ymin) + ", " + str(xmax) + ", " + str(ymax)
            req.setParameter('BBOX', coords)
            status = map.OWSDispatch( req )

            assert status == 0
            headers = mapscript.msIO_getAndStripStdoutBufferMimeHeaders()
            assert headers is not None
            assert 'Content-Type' in headers
            assert headers['Content-Type'] == 'image/png'

            result = mapscript.msIO_getStdoutBufferBytes()
            assert result is not None
            assert result[1:4] == b'PNG'

            if SumaLongitudes < img_length :
                output_file = fN_pattern_noOrtho.format( i+1, j+1)
            else:
                output_file = fN_pattern_yesOrtho.format( i+1, j+1)
                contador = contador + 1 
            with open(output_file, "wb") as f:
                f.write(result)            

            req.setParameter('LAYERS','viales')
            status = map.OWSDispatch( req )

            assert status == 0
            headers = mapscript.msIO_getAndStripStdoutBufferMimeHeaders()
            assert headers is not None
            assert 'Content-Type' in headers
            assert headers['Content-Type'] == 'image/png'

            result = mapscript.msIO_getStdoutBufferBytes()
            assert result is not None
            assert result[1:4] == b'PNG'

            if SumaLongitudes < img_length :
                output_file = fN_pattern_noWMS.format( i+1, j+1)
            else:
                output_file = fN_pattern_yesWMS.format( i+1, j+1)
            with open(output_file, "wb") as f:
                f.write(result)            
            
               

        gdal.TermProgress( i / float(filasarea)  )
    print("--- Processed (%d) tiles from sheet (%s, identified %d candidate tiles in %s hours ---" % ((filasarea * columnasarea),fName, contador,(time.time() - start_time)/3600))        

