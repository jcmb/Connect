#! /usr/bin/env python -u

from pprint import pprint
import logging
import logging
import logging.handlers
from logging import NullHandler
import sys
import argparse
import os
import glob
import traceback
import time

#logging.getLogger(__name__).addHandler(NullHandler())
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
syslog_handler = logging.handlers.SysLogHandler()
logger.addHandler(handler)
logger.addHandler(syslog_handler)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

#logging.getLogger(__name__).addHandler(NullHandler())
#logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

#sys.path.append("Connect_Lib"); # Needed for the 

from Connect import Connect

def create_arg_parser():
    usage="Connect_Upload.py [user] [password] <Project_Name> <Files or Pattern>"
    parser=argparse.ArgumentParser(prog="Connect_Upload.py")
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.1')
    parser.add_argument("project", type=str, help="Project Name")
    parser.add_argument("folder", type=str, help="Folder in Project")
    parser.add_argument("files", nargs="*", help="Files to upload")
    parser.add_argument("-T", "--tell",action="store_true", dest="tell", default=False, help="Tell the settings for the run")
    parser.add_argument("-R", "--recurse",action="store_true", dest="recurse", default=False, help="Recurse down folders" )
    parser.add_argument("-a", "--age",type=int, dest="age", default=0,help="Only transfer files that are older than this number of hours.")
    parser.add_argument("-l", "--location",type=str, dest="location", default="us", help="The Connect pod location. (us,europe,asia) Default=us.")
    parser.add_argument("-u", "--user", required=True,type=str, dest="user", help="The Connect username.")
    parser.add_argument("-p", "--password", required=True,type=str, dest="password", help="The Connect password.")
    parser.add_argument("-d", "--delete", action="store_true", dest="delete", help="Delete after file upload. (No Cache) Delete file if exists in connect already (cached)")
    parser.add_argument("-g", "--glob",type=str, dest="glob", help="File search pattern. On linux make sure you have \" \" around the glob")
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
    RECURSE=options.recurse
    LOCATION=options.location
    FOLDER=options.folder
    FILES=options.files
    GLOB=options.glob
    DELETE=options.delete
    CACHE=not options.no_cache
    AGE=options.age
    
    if GLOB and FILES != []:
        sys.exit("Error: You can not use GLOB and provide FILES at the same time")

    if GLOB ==None and FILES==[]:
        sys.exit("Error: You must provide either GLOB or FILES")
        
    if FILES==[]:
      FILES=None

    if options.tell:
        print "Project: " + PROJECT
        print "Folder: " + FOLDER
        print "Files: " + str(len(FILES))
        print "Glob: " + str(GLOB)
        print "File Age: " + str(AGE)
        print "Recurse: " + str(RECURSE)
        print "Use Cache (Check MD5 Hash): " + str(CACHE)
        print "Delete after Transfer: " + str(DELETE)
        print "Location: " + LOCATION
        print "User: " +  options.user
        print "Verbose: " + str(VERBOSE)
        
    
    return (PROJECT,LOCATION, FOLDER, FILES, GLOB, AGE, DELETE, CACHE,RECURSE,VERBOSE,options.user,options.password)

def subfolderId_from_subfolders(subfolder,subfolders):
#  pprint (subfolders)
  subfolderId=None 
  subfolder=subfolder.lower()
#  print "Looking for: " + subfolder
  for item in subfolders:
#    pprint (subfolders[item]["name"])
    if subfolders[item]["name"].lower() == subfolder:
       subfolderId=subfolders[item]["id"]
       break
  return(subfolderId)     

    
def upload_files_and_folders(TC,projectId,PROJECT, folderId,FOLDER_PATH,FILES,GLOB,AGE, DELETE,CACHE,RECURSE,VERBOSE):
#  traceback.print_stack()
#  pdb.set_trace()
#  print ("{}: {}".format(projectId,PROJECT))
#  print ("{}: {}".format(folderId,FOLDER_PATH))
#  print os.getcwd()
#  pprint (FILES)
  connect_files={}
  subfolders={}
  if CACHE:
    if VERBOSE:
      sys.stderr.write("Getting Information from connect for folder {}\n".format(FOLDER_PATH))
    connect_contents= TC.get_children(folderId)
    connect_files=TC.files_only(connect_contents)
    subfolders=TC.folders_only(connect_contents)
    if VERBOSE:
      sys.stderr.write("Got Information from connect for folder {}\n".format(FOLDER_PATH))
  else:
    if RECURSE:    
      DIRS=os.listdir(".")
      if VERBOSE:
        sys.stderr.write("Getting subfolder Information from connect for folder {}\n".format(FOLDER_PATH))
      subfolders=TC.get_folders(projectId,folderId)
      if VERBOSE:
        sys.stderr.write("Got sub folder Information from connect for folder {}\n".format(FOLDER_PATH))

  
#  pprint(connect_files)
  if FILES ==None: #Did not get files passed so use the GLOB to get them
    print "GLOB: " + GLOB
    LOCAL_FILES= glob.glob(GLOB)
  else:
    print "FILES: " + str(FILES)
    LOCAL_FILES=FILES # WE use Local files to make sure that we continue to use the GLOB

    
  for file in LOCAL_FILES: 
    if os.path.isfile(file):
      local_filename=os.path.basename(file)
      if VERBOSE>2:
        sys.stderr.write("File: {}\n".format(file ))

      fileTime=os.path.getmtime(file)
      fileDelta=time.time() - fileTime   
      
      if fileDelta < AGE*3600:
        if VERBOSE>=2:
           sys.stdout.write("Skipped as too new\n")
        continue

      if CACHE and (local_filename in connect_files):
        sys.stdout.write("Updating: {} in {}:{}, ".format(file,PROJECT,FOLDER_PATH))
        (result,task)=TC.upload_file(projectId,folderId,file,connect_files[local_filename]["hash"],connect_files[local_filename]["size"])
        sys.stdout.write("{}.".format(task))        
        if result:
          if task == "Cached":
            if DELETE:
               os.remove(file)
               sys.stdout.write(" Deleted. ")
          else: 
             sys.stdout.write("Error: " +task)
        else: 
           sys.stdout.write("Upload Failed. ")
      else: 
        sys.stdout.write("New Upload: {} to {}, ".format(file,FOLDER_PATH))
        (result,task)=TC.upload_file(projectId,folderId,file,None,None)
        if result:
          if task == "Uploaded":        
            if DELETE:
               sys.stdout.write("Uploaded. ")
               os.remove(file)
               sys.stdout.write("Deleted. ")
            else: 
               sys.stdout.write("Uploaded. ")
          else: 
             sys.stdout.write("Error: " +task)
        else: 
           sys.stdout.write("Upload Failed. ")
        
      sys.stdout.write("\n")

  if RECURSE:    
    DIRS=os.listdir(".")
  else:
    DIRS=[]
    
  for dir in DIRS:     
    if os.path.isdir(dir) and RECURSE:
      logger.info("Directory: "+dir)
      
      if dir[0]==".":
        logger.info("Skipping Directory that starts with .: {}\n".format(dir))
        if VERBOSE:
          sys.stdout.write("Skipping Directory that starts with .: {}\n ".format(dir))
        continue
       
      
      if FOLDER_PATH=="/":
        subfolderId=TC.get_folderId_by_path(projectId,PROJECT,dir) #This one is always fast
        new_FOLDER_PATH=dir
      else:
        new_FOLDER_PATH=FOLDER_PATH+"/"+dir
        subfolderId=subfolderId_from_subfolders(dir,subfolders)
#        subfolderId=TC.get_folderId_by_path(projectId,PROJECT,new_FOLDER_PATH) # This can be super slow for folders with lots of files
        
        
      if subfolderId != None:
        sys.stdout.write("Directory: {}\n".format(new_FOLDER_PATH))
      else:
        sys.stdout.write("Create Directory: {}\n".format(new_FOLDER_PATH))
        subfolderId=TC.create_folder(projectId,folderId,dir)
        
        if subfolderId == None:
           logger.critical("could not create folder {} {} Project:{} Folder:{}".format(new_FOLDER_PATH,dir,projectId,folderId))
           sys.exit("could not create folder {} {} Project:{} Folder:{}".format(new_FOLDER_PATH,dir,projectId,folderId))

      logger.info("folderID: "+subfolderId)
      logger.debug("Changing directory to : "+dir)          
      os.chdir(dir)
      logger.debug("Directory is : "+os.getcwd())          
      
      if GLOB==None: # If we did not get a GLOB passed then do all of the files in the sub folder
        upload_files_and_folders(TC,projectId,PROJECT,subfolderId,new_FOLDER_PATH,glob.glob("*"),None,AGE,DELETE,CACHE,RECURSE,VERBOSE)
      else:  #Got a Glob, do not pass any files pass the GLOB 
        upload_files_and_folders(TC,projectId,PROJECT,subfolderId,new_FOLDER_PATH,None,GLOB,AGE,DELETE,CACHE,RECURSE,VERBOSE)
      os.chdir("..")
      logger.debug("Directory is : "+os.getcwd())          
      logger.debug("Back from sub directory upload")

      if VERBOSE:
        sys.stdout.write("Back from sub directory to Directory: {}\n".format(FOLDER_PATH))

      


def main():
  (PROJECT,LOCATION, FOLDER, FILES, GLOB, AGE, DELETE, CACHE, RECURSE,VERBOSE,USER,PASSWORD) = process_arguments()
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

#  subfolders=TC.get_folders(projectId,folderId)

  upload_files_and_folders(TC,projectId,PROJECT,folderId,FOLDER,FILES,GLOB,AGE, DELETE,CACHE,RECURSE,VERBOSE)
   
  logger.info("Logging out")

  TC.logout()


main()