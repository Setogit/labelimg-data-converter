# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 Tetsuo Seto

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse, glob, os, re, shutil
from random import random
import xml.etree.ElementTree as ET

parser = None
classes = None
source_dir = None
destination_dir = None
dest_subdir = None
dest_file_name_header = None
percentage_test = None

class ImageData(object):
    """Original source of the annotated image files and labelimg-generated meta data XML files

    Restructuring is the following: search input_dir for labelimg-generated meta data XML files.
    The input_dir directory has subdirectories "movie*" where * is one or more digits.
    
    In each "movie" subdirectory, there are meta data *.xml files and associated *.jpg files
    where * is "frame" + three of four digit characters.  For example,
    movie23/frame003.xml and movie23/frame003.jpg

    First, for each XML file, sanitized xml_id is determined and file names are determined.

    Meta data XML files and JPG image files with the sanitized names are copied over to output_dir.

    The XML file extension and the image file extension MUST be .xml and .jpg respectively.

    If there are no XML files, associated *.jpg files are not copied.

    Attributes:
        input_dir: directory where the input image files and associated labelimg-generated
        meta data XML files reside under subdirectory, i.e., two-level directory structure
        such as <input_dir>/movie12/frame003.xml and <input_dir>/movie12/frame003.jpg.

        file_header: used as the header of the output xml and jpg.

        output_dir: directory where the input image files and associated labelimg-generated
        meta data XML files are stored in a flat directory structure.  For example,
        <output_dir>/<file_header>12_frame0003.xml and <output_dir>/<file_header>12_frame0003.jpg
    """

    def __init__(self, input_dir, output_dir, file_header, existence_check_when_copying = False):
      """Initializes ImageData"""
      self.input_dir = input_dir
      self.output_dir = output_dir
      self.file_header = file_header
      self.copied_pairs_count = 0
      self.existence_check_when_copying = existence_check_when_copying

    def sanitize_id(self, xml):
      """Sanitize the xml file name trailer
      xml is the XML file name (or full path) which ends with <three or four digits> + '.xml'
      returns a string of sanitized version of 4-digit id, for example, if xml ends with
      frame1425.xml, sanitize_id returns 1425.  In case sanitize_id is frame023.xml, returns 0023.
      """
      xml_id = xml[-8:].split('.xml')[0]
      if not xml_id.isdigit():
        xml_id = '0' + xml_id[1:]
      assert(xml_id.isdigit())
      assert(len(xml_id) == 4)
      return xml_id

    def sanitize(self):  
      """Reads *xml and associated *.jpg, sanitizes file names, and copies the xml and jpg files
      to the output_dir.

      Changes directory structure from two to one and streamline the file names.  It does not
      modify the contents of xml and jpg files.
      """
      self.copied_pairs_count = 0
      for movie_dir in glob.iglob(os.path.join(self.input_dir, 'movie*')):
        movie_dir_name = os.path.split(movie_dir)[1]
        movie_dir_id = movie_dir_name.split('movie')[1]
        # print(movie_dir, movie_dir_name, movie_dir_id)
        proper_file_name_head = self.file_header + movie_dir_id + '_' + 'frame'
        for xml in glob.iglob(os.path.join(movie_dir, '*.xml')):
          jpg_path = xml.split('.xml')[0] + '.jpg'
          jpg_exists = os.path.exists(jpg_path)
          if not jpg_exists:
            print('***** JPG is missing: {}'.format(jpg_path))
            continue
          xml_name = os.path.split(xml)[1]
          xml_id = self.sanitize_id(xml_name)
          proper_xml_name = proper_file_name_head + xml_id + '.xml'
          if self.existence_check_when_copying and os.path.exists(os.path.join(self.output_dir, proper_xml_name)):
            print('***** already exists: {} where src: {}'.format(proper_xml_name, xml))
          proper_jpg_name = proper_file_name_head + xml_id + '.jpg'
          if self.existence_check_when_copying and os.path.exists(os.path.join(self.output_dir, proper_jpg_name)):
            print('***** already exists: {} where src: {}'.format(proper_jpg_name, jpg_path))
          dst_html = os.path.join(self.output_dir, proper_xml_name)
          shutil.copyfile(xml, dst_html)
          dst_jpg = os.path.join(self.output_dir, proper_jpg_name)
          # print(jpg_path + ' to ' + dst_jpg)
          shutil.copyfile(jpg_path, dst_jpg)
          self.copied_pairs_count += 1

class MetaData(object):
    """Converter to read labelimg meta data (xml) and write Yolo meta data (txt)

    LabelImg is open source data image labeling utility (https://github.com/tzutalin/labelImg)
    LabelImg writes the label meta data as a XML file.  For details, please refer to
    the github repository.

    Yolo meta data is simple ASCII txt file.  Each line corresponds to one object.
    The object meta-data line contain one integer value followed by four float values.

    int [class id]
    float[0.0 .. 1.0] [object center in X]
    float[0.0 .. 1.0] [object center in Y]
    float[0.0 .. 1.0] [object width in X]
    float[0.0 .. 1.0] [object width in Y]

    Attributes:
        classes: dictionary that maps class name to class id (integer)
          e.g. classes = {'hoe': 0, 'body': 1, 'wheels': 2}
    """

    def __init__(self, classes):
      """Initializes MetaData"""
      self.classes = classes

    def convert(self, xml):  
      """Parse the input "xml" file to an XML tree in memory.
      xml is a full file path ending with '.xml'
      The output .txt file is created in the same directory with the same
      name + '.txt'  
      return True if one or more objects are defined in the XML
      return False if no valid objects are found
      """
      txt_path, ext = os.path.splitext(xml)
      assert(ext == '.xml')
      assert(txt_path != '')
      txt_path = txt_path + '.txt'
      tree = ET.parse(xml)
      root = tree.getroot()
      assert(root.tag == 'annotation') # validate the root tag of the input XML
      img_width = None # width of the image in pixels (int)
      img_height = None # height of the image in pixels (int)
      for size in root.iter('size'): # search for "size" node underneath root
        assert(int(size.find('depth').text) == 3) # validate that the depth is 3
        assert(img_width == None) # there must be only one img_width defined in the xml
        img_width = int(size.find('width').text)
        assert(img_height == None) # there must be only one img_width defined in the xml
        img_height = int(size.find('height').text)
      assert(img_width > 0)
      assert(img_height > 0)
      obj_data = '' # object meta-data string in yolo format; directly written to the yolo TXT file
      for obj in root.iter('object'): # search for "object" node underneath root
        name = obj.find('name').text
        if name not in self.classes:
          # if the name in the object node is not defined in the classes,
          # print the error and continue to search for the next object node.
          print('***** "{}"" is wrong class in {}'.format(name, xml))
          continue
        class_id = self.classes[name]
        for bndbox in obj.iter('bndbox'): # search for "bndbox" node underneath the object node
          # read the four integer values from the object node in XML
          xmin = int(bndbox.find('xmin').text)
          assert(xmin > 0)
          xmax = int(bndbox.find('xmax').text)
          assert(xmax > 0)
          ymin = int(bndbox.find('ymin').text)
          assert(ymin > 0)
          ymax = int(bndbox.find('ymax').text)
          assert(ymax > 0)
          abs_width = float(xmax - xmin) # width of the annotated object
          abs_height = float(ymax - ymin) # height of the annotated object
          xcenter = (abs_width/2 + xmin)/img_width
            # relative X position of the center of the object in the image
          ycenter = (abs_height/2 + ymin)/img_height
            # relative Y position of the center of the object in the image
          rel_width = abs_width/img_width # relative width of the object in the image
          rel_height = abs_height/img_height # relative height of the object in the image
          # append the object meta data in yolo format to the object meta-data string
          obj_data += (str(class_id) + ' ' + str(xcenter) + ' ' +
            str(ycenter) + ' ' + str(rel_width) + ' ' + str(rel_height))
          obj_data += '\n'
          xmin = xmax = ymin = ymax = None # reset to None
      if obj_data == '':
        # if no valid objects found, return False
        print('----- object is empty: {}'.format(xml))
        return False
      else:
        txt_file = open(txt_path, 'w')
        txt_file.write(obj_data)
        txt_file.close()
        return True

class TrainingData(object):
    """Split the sanitized image data and meta data files into two sets: train and test
    and the two lists of the JPG file names are stored in <header>-train.txt and
    <header>-test.txt files under <output_dir> directory.

    Attributes:
        file_header: directory where the input image files and associated yolo meta data
        TXT files reside.

        input_dir: directory where the input JPG image files and associated yolo meta data
        TXT files reside.

        output_dir: directory where <header>-train.txt and  <header>-test.txt files are stored.

        percentage_test: split (0.0 .. 1.0) exclusive
    """

    def __init__(self, input_dir, output_dir, file_header, classes, percentage_test):
      """Initializes TrainData"""
      self.input_dir = input_dir
      self.output_dir = output_dir
      self.file_header = file_header
      assert(0.0 < percentage_test and percentage_test < 1.0)
      self.percentage_test = percentage_test
      self.classes = classes
      self.detected_pairs_count = 0
      self.processed_count = 0

    def split(self):
      """Split TrainData"""
      self.detected_pairs_count = 0
      self.processed_count = 0
      metaData = MetaData(self.classes)
      file_train = open(os.path.join(self.output_dir, self.file_header + '-train.txt'), 'w')
      file_test = open(os.path.join(self.output_dir, self.file_header + '-test.txt'), 'w')
      for xml in glob.iglob(os.path.join(self.input_dir, '*.xml')):
        jpg_path = xml.split('.xml')[0] + '.jpg'
        xml_file_name = os.path.split(xml)[1]
        jpg_file_name = os.path.join(self.input_dir, xml_file_name.split('.xml')[0] + '.jpg') + '\n'
        jpg_exists = os.path.exists(jpg_path)
        if jpg_exists:
          self.detected_pairs_count += 1
          processed = metaData.convert(xml)
          if processed:
            if random() < self.percentage_test:
              file_test.write(jpg_file_name)
            else:
              file_train.write(jpg_file_name)
            self.processed_count += 1
        else:
          print('***** JPG is missing: {}'.format(jpg_path))
      file_train.close()
      file_test.close()

def main():
  global classes, source_dir, destination_dir
  global dest_subdir, dest_file_name_header, percentage_test
  current_dir = os.path.abspath('./')
  input_dir = os.path.join(current_dir, source_dir)
  output_dir = os.path.join(current_dir, os.path.join(destination_dir, dest_subdir))
  imageData = ImageData(input_dir, output_dir, dest_file_name_header)
  imageData.sanitize();
  print('_____ {} xml/jpg pairs have been copied.'.format(imageData.copied_pairs_count))
  input_dir = output_dir
  output_dir = os.path.join(current_dir, destination_dir)
  trainData = TrainingData(input_dir, output_dir, dest_subdir, classes, percentage_test)
  trainData.split()
  print('_____ {} JPG/XML pairs were detected in "{}".'.format(trainData.detected_pairs_count, source_dir))
  if imageData.copied_pairs_count == trainData.detected_pairs_count:
    print('_____ All the JPG/XML pairs were examined.')
  else:
    print('***** Some JPG/XML pairs were missing.')
  print('_____ {} valid JPG/XML/TXT trios were generated in "{}/{}".'.format(trainData.processed_count, destination_dir, dest_subdir))

class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __eq__(self, other):
        return self.start <= other <= self.end
    def __repr__(self):
        return '({} .. {}) exclusive'.format(self.start, self.end)

def parse_args():
  global parser, classes
  global source_dir, destination_dir, dest_subdir, dest_file_name_header
  global percentage_test

  parser = argparse.ArgumentParser(usage='python labelimg_data_converter.py <comma delimited list of class names> such as "cat,dog,horse,pig"', 
    description='Converts labelimg meta data to yolo meta data. \
The original image files (*.jpg) and lalbelimg meta data XML files (*.xml) \
must exist in sub-directories named "movie<M_ID>" where <M_ID> is \
an positive integer number.  \
In the sub-directories, the jpg and xml files must exist with file names \
as "frame<F_ID>.jpg" and "frame<F_ID>.xml" where <F_ID> is either \
3- or 4-digit number.  For example, <source_dir>/movie1/frame001.xml \
or <source_dir>/movie123456/frame1234.xml')
  parser.add_argument('classes', action='store', type=str,
                      help='[REQUIRED] a comma delimited list of class names; \
                      THE ORDER IS IMPORTANT because the 0-based index is used as \
                      class id in the model. \
                      e.g., cat,dog,horse,pig is translated as \
                      {"cat": 0, "dog": 1, "horse": 2, "pig": 3}')
  parser.add_argument('-s', '--source', action='store', type=str, default='source',
                      dest='src',
                      help='directory where the original labelimg meta data XML \
                      and image JPG files resides.  \
                      default: "source"')
  parser.add_argument('-d', '--destination', action='store', type=str, default='destination',
                      dest='dest',
                      help='directory where the sanitized and converted yolo meta data TXT \
                      and image JPG as well as the original labelimg meta data XML will \
                      be stored.  \
                      default: "destination"')
  parser.add_argument('-b', '--subdir', action='store', type=str, default='data',
                      dest='subdir',
                      help='sub-directory where the generated files are stored beneath \
                      the destination directory.  \
                      default: "data"')
  parser.add_argument('-e', '--header', action='store', type=str, default='sample',
                      dest='header',
                      help='string used as header of the generated yolo meta data TXT file names.  \
                      default: "sample"')
  parser.add_argument('-p', '--percentage_test', action='store', type=float,
                      choices=[Range(0.0, 1.0)], default=0.1, dest='percent',
                      help='float number between 0.0 and 1.0 exclusive to specify the amount of \
                      labeled images to be used for validation in training. \
                      default: 0.1, which means 10 percent.')

  args = parser.parse_args()
  source_dir = args.src
  destination_dir = args.dest
  dest_subdir = args.subdir
  dest_file_name_header = args.header
  percentage_test = args.percent
  assert(args.classes != None)
  classes = {}
  args.classes = re.sub('[\s+]', '', args.classes)
  for i,v in enumerate(args.classes.split(',')):
    classes[v] = i


if __name__ == "__main__":
    parse_args()
    main()
