#! /usr/bin/env python -u

from pprint import pprint
import logging
from logging import NullHandler
import sys
import argparse
import os
import glob
import traceback
import pdb

logging.getLogger(__name__).addHandler(NullHandler())
logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

#sys.path.append("Connect_Lib"); # Needed for the 

from Connect import Connect

def create_arg_parser():
    usage="Connect_Upload.py [user] [password] <Project_Name> <Folder>"
    parser=argparse.ArgumentParser()
    parser.add_argument("project", type=str, help="Project Name")
    parser.add_argument("folder", type=str, help="Folder in Project")
    parser.add_argument("files", nargs="+", help="Files to upload")
    parser.add_argument("-T", "--tell",action="store_true", dest="tell", default=False, help="Tell the settings for the run")
    parser.add_argument("-l", "--location",type=str, dest="location", default="us", help="The Connect pod location. (us,europe,asia) Default=us.")
    parser.add_argument("-u", "--user", required=True,type=str, dest="user", help="The Connect username.")
    parser.add_argument("-p", "--password", required=True,type=str, dest="password", help="The Connect password.")
    parser.add_argument("-d", "--delete", action="store_true", dest="delete", help="Delete after file upload. (No Cache) Delete file if exists in connect already (cached)")
    parser.add_argument("-n", "--no-cache", action="store_true", dest="no_cache", help="Delete after file upload")
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
    FOLDER=options.folder
    FILES=options.files
    DELETE=options.delete
    CACHE=not options.no_cache

    if options.tell:
        print "Project: " + PROJECT
        print "Folder: " + FOLDER
        print "Files: " + str(FILES)
        print "Use Cache (Check MD5 Hash): " + str(CACHE)
        print "Delete after Transfer: " + str(DELETE)
        print "Location: " + LOCATION
        print "User: " +  options.user
        
    
    return (PROJECT,LOCATION, FOLDER, FILES, DELETE, CACHE,VERBOSE,options.user,options.password)

    
def upload_files_and_folders(TC,projectId,PROJECT, folderId,FOLDER_PATH,FILES,DELETE,CACHE,RECURSE):
#  traceback.print_stack()
#  pdb.set_trace()
#  print ("{}: {}".format(projectId,PROJECT))
#  print ("{}: {}".format(folderId,FOLDER_PATH))
#  print os.getcwd()
#  pprint (FILES)
  
  
  connect_contents= TC.get_children(folderId)
  connect_files=TC.files_only(connect_contents)
  connect_folder=TC.folders_only(connect_contents)
  
#  pprint(connect_files)
#TODO This is not documented at all
  for file in FILES: 
    if os.path.isdir(file) and RECURSE:
      logger.info("Directory: "+file)
      
      if FOLDER_PATH=="/":
        subfolderId=TC.get_folderId_by_path(projectId,PROJECT,file)
        new_FOLDER_PATH=file
      else:
        new_FOLDER_PATH=FOLDER_PATH+"/"+file
        subfolderId=TC.get_folderId_by_path(projectId,PROJECT,new_FOLDER_PATH)
        
      sys.stdout.write("Directory: {}\n".format(new_FOLDER_PATH))
        
      if subfolderId == None:
        subfolderId=TC.create_folder(projectId,folderId,file)
        
        if subfolderId == None:
           logger.critical("could not create folder {}".format(file))
           sys.exit("could not create folder {}".format(file))

      logger.info("folderID: "+subfolderId)
      logger.debug("Changing directory to : "+file)          
      os.chdir(file)
      upload_files_and_folders(TC,projectId,PROJECT,subfolderId,new_FOLDER_PATH,glob.glob("*"),DELETE,CACHE,RECURSE)
      os.chdir("..")
      logger.debug("Back from sub directory upload")
      sys.stdout.write("Directory: {}\n".format(FOLDER_PATH))

#      print ("{}: {}".format(projectId,PROJECT))
#      print ("{}: {}".format(folderId,FOLDER_PATH))
#      print os.getcwd()
#      pprint (FILES)
          

      
    if os.path.isfile(file):
      local_filename=os.path.basename(file)
      if CACHE and (local_filename in connect_files):
        sys.stdout.write("Updating: {} in {}:{}, ".format(file,PROJECT,FOLDER_PATH))
        (result,task)=TC.upload_file(projectId,folderId,file,connect_files[local_filename]["hash"],connect_files[local_filename]["size"])
        sys.stdout.write("{}.".format(task))        
        if task == "Cached":
          if DELETE:
             os.remove(file)
             sys.stdout.write(" Deleted. ")
      else: 
        sys.stdout.write("New Upload: {} to {}, ".format(file,FOLDER_PATH))
        TC.upload_file(projectId,folderId,file,None,None)
        
        if DELETE:
           sys.stdout.write("Uploaded. ")
           os.remove(file)
           sys.stdout.write("Deleted. ")
        else: 
           sys.stdout.write("Uploaded. ")
      sys.stdout.write("\n")



def main():
  (PROJECT,LOCATION, FOLDER, FILES, DELETE, CACHE, VERBOSE,USER,PASSWORD) = process_arguments()
  TC=Connect(USER,PASSWORD,VERBOSE)

  Logged_In = TC.Login()

  if Logged_In:
    logger.info("Logged in as {}".format(USER))
  else:
    logger.info("Login in as {} failed".format(USER))
    sys.exit("Login failed")

  TC.set_projects_area(LOCATION) 
  projectId=(TC.get_project_by_name(PROJECT))

  if projectId == None:
    logger.critical("Did not find Project")
    sys.exit("Did not find Project")
  else: 
    logger.info("projectID: "+projectId)
    
  folderId=TC.get_folderId_by_path(projectId,PROJECT,FOLDER)
  if folderId == None:
    logger.critical("Did not find folder")
    sys.exit("Did not find folder")
  else: 
    logger.info("folderID: "+folderId)

  RECURSE=True
  upload_files_and_folders(TC,projectId,PROJECT,folderId,FOLDER,FILES,DELETE,CACHE,RECURSE)
   
  logger.info("Logging out")

  TC.logout()


main()