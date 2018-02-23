# labelimg-data-converter
Converts labelimg meta data to yolo format.  See https://github.com/tzutalin/labelImg

```
$ python labelimg_data_converter.py -h
usage: python labelimg_data_converter.py <comma delimited list of classs names> such as "cat,dog,horse,pig"

Converts labelimg meta data to yolo meta data. The original image files
(*.jpg) and lalbelimg meta data XML files (*.xml) must exist in sub-
directories named "movie<M_ID>" where <M_ID> is an positive integer number. In
the sub-directories, the jpg and xml files must exist with file names as
"frame<F_ID>.jpg" and "frame<F_ID>.xml where <F_ID> is either 3- or 4-digit
number. For example, <source_dir>/movie1/frame001.xml or
<source_dir>/movie123456/frame1234.xml

positional arguments:
  classes               [REQUIRED] a comma delimited list of
                        class_name:class_id pairs. space characters are
                        preserved. e.g., "dog:1,cat:0,horse:3,peter rabbit:5"
                        is translated to {"cat": 0, "dog": 1, "horse": 3,
                        "peter rabbit": 5}

optional arguments:
  -h, --help            show this help message and exit
  -s SRC, --source SRC  directory where the original labelimg meta data XML
                        and image JPG files resides. default: "source"
  -d DEST, --destination DEST
                        directory where the sanitized and converted yolo meta
                        data TXT and image JPG as well as the original
                        labelimg meta data XML will be stored. default:
                        "destination"
  -b SUBDIR, --subdir SUBDIR
                        sub-directory where the generated files are stored
                        beneath the destination directory. default: "data"
  -e HEADER, --header HEADER
                        string used as header of the generated yolo meta data
                        TXT file names. default: "sample"
  -p {(0.0 .. 1.0) exclusive}, --percentage_test {(0.0 .. 1.0) exclusive}
                        float number between 0.0 and 1.0 exclusive to specify
                        the amount of labeled images to be used for validation
                        in training. default: 0.1, which means 10 percent.
```