#! /usr/bin/env python -u

from pprint import pprint
import logging
from logging import NullHandler
import sys
import argparse
import os

logging.getLogger(__name__).addHandler(NullHandler())
logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

sys.path.append("Connect_Lib"); # Needed for the 
sys.path.append("../Connect_Lib"); # Needed for the 

from Connect import Connect

def create_arg_parser():
    usage="Connect_Download.py [user] [password] <Project_Name> "
    parser=argparse.ArgumentParser()
    parser.add_argument("project", type=str, help="Project Name")
    parser.add_argument('-t', '--type', nargs='+', metavar='EXTENSIONs',
                   help='file types to be downloaded')
    parser.add_argument("-T", "--tell",action="store_true", dest="tell", default=False, help="Tell the settings for the run")
    parser.add_argument("-l", "--location",type=str, dest="location", default="us", help="The Connect pod location. (us,europe,asia) Default=us.")
    parser.add_argument("-u", "--user", required=True,type=str, dest="user", help="The Connect username.")
    parser.add_argument("-p", "--password", required=True,type=str, dest="password", help="The Connect password.")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                   help='increase output verbosity (use up to 3 times)')
    
    return (parser)

def process_arguments ():
    parser=create_arg_parser()
    options = parser.parse_args()
#    print options
    VERBOSE=options.verbose
    PROJECT=options.project
    LOCATION=options.location

    if options.tell:
        print "Project: " + PROJECT
        print "Location: " + LOCATION
        print "User: " +  options.user
        
    
    return (PROJECT,LOCATION, VERBOSE,options.user,options.password,options.type)

def download_dir_and_children(TC,ProjectId, FolderId,Folder_Path,file_Extensions_Filter, VERBOSE):
  logger.debug("Download dir and children: {} {} {} {}".format,ProjectId,FolderId,Folder_Path,file_Extensions_Filter)
  if os.path.isfile(Folder_Path):
    raise ("File exists for directory to be created: " + Folder_Path)
  elif os.path.isdir(Folder_Path):
    logger.info("Directory already exists for: " + Folder_Path)
  else:
    if VERBOSE :
      print "Making Directory: " + Folder_Path
      logger.info("Making Directory: " + Folder_Path)
    os.mkdir(Folder_Path)
    
    
  items=TC.get_children(ProjectId,FolderId)
  files=TC.files_only(items)
  folders=TC.folders_only(items)
  
  for file_index in files:
    Extension_Found=True
    filename=files[file_index]["name"]
    if file_Extensions_Filter!=None:
      Extension_Found=False
      for extension in file_Extensions_Filter:
        substr_location= filename.find(extension,-len(extension))
        if substr_location != -1 :
#          print substr_location, len(extension),len(filename),filename
          Extension_Found=True
          break
    
    
    
    if Extension_Found:
      hash= files[file_index]["hash"]
      print "Download file: {} ({}), ".format(Folder_Path+'/'+filename,file_index,hash),
      logger.info("Download file: {} ({}) [{}]".format(Folder_Path+'/'+filename,file_index,hash))
      (Success,Message)=TC.download_file(ProjectId,file_index,Folder_Path+'/'+filename,hash)
      logger.info("{} ({})".format(Success,Message))
      print Message
    else:
      logger.debug("Skipping file with wrong extension: {} ({})".format(filename,file_index))
    

  for folder_index in folders:
    logger.debug("Folder: {} ({})".format(folders[folder_index]["name"],folder_index))
#    pprint (folders[folder_index])
    download_dir_and_children(TC,ProjectId,folder_index,Folder_Path+"/"+folders[folder_index]["name"],file_Extensions_Filter,VERBOSE)
    

def main():
  (PROJECT,LOCATION, VERBOSE,USER,PASSWORD,EXTENSIONS) = process_arguments()
  TC=Connect(USER,PASSWORD)

  Logged_In = TC.Login()

  if Logged_In:
    logger.info("Logged in as {}".format(USER))
  else:
    print "Login failed"
    sys.exit(1)

  TC.set_projects_area(LOCATION) 
  projects=(TC.get_projects())

  ProjectId=None
  for project_index in projects:
    if projects[project_index]["name"].lower()==PROJECT.lower():
      logger.debug("Found Project")
#      pprint ( projects[project_index])
      ProjectId=project_index
      RootId=projects[project_index]["rootId"]

  if ProjectId != None:
    download_dir_and_children(TC,ProjectId,RootId,".",EXTENSIONS,VERBOSE)
  else:
    logger.critical("Did not find Project")
    print "Did not find Project"


  logger.info("Logging out")

  TC.logout()


main()