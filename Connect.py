#! /usr/bin/env python -u

from urlparse import urlparse, parse_qs
import requests
from pprint import pprint
import logging
from logging import NullHandler
import os
import hashlib
from copy import deepcopy
import sys

logging.getLogger(__name__).addHandler(NullHandler())
logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)




BASE_URL="https://app.connect.trimble.com/"
EUROPE_BASE_URL="https://app21.connect.trimble.com/"
ASIA_BASE_URL="https://app31.connect.trimble.com/"


API_URL=BASE_URL+"tc/api/2.0/"
EUROPE_API_URL=EUROPE_BASE_URL+"tc/api/2.0/"
ASIA_API_URL=ASIA_BASE_URL+"tc/api/2.0/"

BASE_URL_HTTP="http://app.connect.trimble.com/"
API_URL_HTTP=BASE_URL_HTTP+"tc/app/2.0/"

def json_to_dict(json): # 
  result={}
  for item in json:
    result[item["id"]]=item
  return(result)

class Connect ():
  def __init__(self, user,password,VERBOSE=False):
    self.user=user
    self.password=password
    self.Cookies=None
    self.session_token=None
    self.xsrf_token=None
    self.headers={}
    self.project_URL=API_URL
#    sys.stderr.write("******* Connect: Verbose: {}***************\n".format(VERBOSE))
    if VERBOSE>=2:
      logging.basicConfig(level=logging.DEBUG)
    


  def me(self):
    r=requests.get(API_URL+"users/me", cookies=self.cookies)
#    pprint (r.status_code)
#    pprint (r.json())
    return(r.status_code==200,r.json())

  def user_by_id(self,id):
    r=requests.get(API_URL+"users/"+id, cookies=self.cookies)
    return(r.status_code==200,r.json())

  def regions(self):
    r=requests.get(API_URL+"regions", cookies=self.cookies,headers=self.headers)
    return(r.json())

  def get_projects(self):
    r=requests.get(self.project_URL+"projects", cookies=self.cookies,headers=self.headers)
    return(json_to_dict(r.json()))
    
  def get_project_by_name(self,ProjectName):
    projects=self.get_projects()
    ProjectName=ProjectName.lower()
    projectId=None
    
    for project_index in projects:
       if projects[project_index]["name"].lower() == ProjectName:
          projectId=projects[project_index]["id"]
          break
    return (projectId)  
          


  def get_project_details(self,projectId):
    r=requests.get(self.project_URL+"projects/"+projectId, cookies=self.cookies,headers=self.headers)
    return(r.json())
    
  def get_project_settings(self,projectId):
#TODO: Documented End point does not exist
    r=requests.get(self.project_URL+"projects/"+projectId+"/settings", cookies=self.cookies,headers=self.headers)
    return(r.json())

    
  def get_project_users(self,projectId):
    r=requests.get(self.project_URL+"projectMemberships?includeRemovedUsers=true&projectId="+projectId, cookies=self.cookies,headers=self.headers)
    return(r.json())
   
  def get_project_roles(self,projectID):
    r=requests.get(self.project_URL+"projectMemberships/roles?projectId="+projectID, cookies=self.cookies,headers=self.headers)
    return(r.json())
    
    
    
  def get_todos(self,projectID):
    r=requests.get(self.project_URL+"todos?projectId="+projectID, cookies=self.cookies,headers=self.headers)
    return(json_to_dict(r.json()))
    
  def get_todo(self,projectID,todoID):
# https://app.connect.trimble.com/tc/app/todos/rLTZG_tO-q0?projectId=7E2ivKgwS5Q
    r=requests.get(self.project_URL+"todos/"+todoID+"?projectId="+projectID, cookies=self.cookies,headers=self.headers)
    return(r.json(  ))


  def get_todo_comments(self,todoID): #Project ID is not required
#    https://app.connect.trimble.com/tc/app/comments?objectId=rLTZG_tO-q0&objectType=TODO&projectId=7E2ivKgwS5Q
    r=requests.get(self.project_URL+"comments?objectType=TODO&objectId="+todoID, cookies=self.cookies,headers=self.headers)
    return(json_to_dict(r.json()))


  def get_folders(self,projectID,parentID):
#TODO This is not documented as needing the project ID  
    r=requests.get(self.project_URL+"folders?parentId="+parentID+"&projectId="+projectID, cookies=self.cookies,headers=self.headers)
    return(json_to_dict(r.json()))
    
  def get_root_folder(self,project_info):
#    print "In get root"
#    pprint (project_info)
    return (project_info["rootId"])
    
  def create_folder(self,projectId,parentId,FolderName):
#    print "In get root"
#    pprint (project_info)
    data={'parentId':parentId,"name":FolderName}
#    print "Headers"
#    pprint (self.headers)
#    pprint (data)

#    r=requests.post("http://httpbin.org/post", json=data,cookies=self.cookies,headers=deepcopy(self.headers))
#    pprint(r.text)
    r=requests.post(self.project_URL+"folders", json=data,cookies=self.cookies,headers=self.headers)
#    print "Reply"
#    pprint (r.text)

    if r.status_code==201:
#       pprint (r.json())
       reply=r.json() #
       return (reply["id"])
    elif r.status_code==409:
       return (self.get_folderId_by_path(projectId,FolderName))
    else:       
       return (None)
    
  def get_children(self,folderId):

    request_size=100
    requesting=True
    start_request_item=0
    children_json={}
    request_headers=deepcopy(self.headers);
    
    while requesting:
       request_headers["Range"]="items={}-{}".format(start_request_item,start_request_item+request_size-1)
       request_headers["Resource-Count"]="true"    
       logger.info("<{}>:\"{}\"".format("Get Children Range",request_headers["Range"]))       
       r=requests.get(self.project_URL+"folders/"+folderId+"/items", cookies=self.cookies,headers=request_headers)
       logger.info("<{}>:\"{}\"".format("Get Children status code",r.status_code))       
       requesting=r.status_code==206
       start_request_item+=request_size
#       pprint (r.headers)
       children_json.update(json_to_dict(r.json()))
      
#    pprint (children_json)
    return(children_json)
    
  def files_only(self,contents_dict):
    result={}
    for contents_index in contents_dict:
      contents=contents_dict[contents_index]
      if contents["type"]=="FILE":
        result[contents["name"]]=contents
    
    return (result)

  def folders_only(self,contents_dict):
    result={}
    for contents_index in contents_dict:
      contents=contents_dict[contents_index]
      if contents["type"]=="FOLDER":
        result[contents_index]=contents
    
    return (result)


#https://app.prod.gteam.com/tc/static/apidoc.html#folders-folder-permissions
  def get_folder_permissions(self,folderID):
#TODO API endpoint   
#    r=requests.get(self.project_URL+"folders/"+folderID+"/permissions", cookies=self.cookies,headers=self.headers)
#    return(r.json())
    return ({})

  def get_folder_contents_by_path(self,projectID,path):
#TODO I can never gert this to work

    r=requests.get(self.project_URL+"folders/by_path?projectId="+projectID+"&path="+path, cookies=self.cookies,headers=self.headers)
#    pprint (r.text)
    return(json_to_dict(r.json()))
    


  def get_folderId_by_path(self,projectId,PROJECT,FOLDER):
    folderId=None
    logger.info("<{}>:\"{}\"".format("get_folderId_by_path Folder",FOLDER))
    projectDetails=self.get_project_details(projectId)
    projectName=projectDetails["name"]

    if FOLDER == "/":
       folderId=projectDetails["rootId"]
       logger.info("<{}>:\"{}\"".format("get_folderId_by_path rootId",folderId))
    else:
       path=os.path.dirname(FOLDER)
       logger.info("<{}>:\"{}\"".format("get_folderId_by_path path",path))
       dir_name=os.path.basename(FOLDER).lower()
       logger.info("<{}>:\"{}\"".format("get_folderId_by_path dir",dir_name))
       if path=="/":
         r=requests.get(self.project_URL+"folders/by_path?projectId="+projectId+"&path="+PROJECT, cookies=self.cookies,headers=self.headers)
       else: 
         r=requests.get(self.project_URL+"folders/by_path?projectId="+projectId+"&path="+PROJECT+'/'+path, cookies=self.cookies,headers=self.headers)
       folder_contents=r.json()
#       pprint (folder_contents)

       for item in folder_contents:
#          pprint (item)
          if item["name"].lower() == dir_name:
             folderId=item["id"]
             break
    logger.info("<{}>:\"{}\"".format("get_folderId_by_path",folderId))
    return (folderId)  
          
       

#    pprint (r.text)
    return(json_to_dict(r.json()))
   
    
#https://app.connect.trimble.com/tc/app/folders?parentId=QS19XFa8lRw&projectId=keiRTYOyDMM
    

#https://app.connect.trimble.com/tc/app/groups?projectId=KKnhMidp_EA
#https://app.connect.trimble.com/tc/app/groupMemberships?projectId=KKnhMidp_EA

  def download_file(self,projectId,fileID,filename,hash=None,size=None):

    if hash != None:
      if os.path.isfile(filename):
        current_hash = hashlib.md5(open(filename, 'rb').read()).hexdigest()
        current_size = os.path.getsize(filename)
        
        if (current_hash == hash) and (current_size == size):
          return (True,"Cached")        
    try :  
      with open(filename, 'wb') as fd:
  # https://app.connect.trimble.com/tc/app/files/download?projectId=VvXFRTbltU4&id=MVSh54l8Ba8
    
          r=requests.get(self.project_URL+"files/download/?projectId="+projectId+"&id="+fileID, cookies=self.cookies,headers=self.headers)
          for chunk in r.iter_content(chunk_size=10000):
              fd.write(chunk)
      return (True,"Downloaded")
    except:
      return (False,"Error")
    
  def upload_file(self,projectId,pathId,filename,hash=None,size=None):
    if os.path.isfile(filename):
      if hash==None  and size == None:
        hash_check=False
        size_check=False
        logger.info("<{}>:{}::\"{}\"".format("upload_file:",filename,"No Size or Hash Checks"))
      else:
        if hash:
          current_hash = hashlib.md5(open(filename, 'rb').read()).hexdigest()
          hash_check=current_hash == hash
          logger.debug("<{}>:{}::\"{}\" {}".format("upload_file:",filename,"Hash Check",hash_check))
        else:
          #If we did not get a hash but did get a size then we pass the check so the other one if the check
          hash_check=not size ==None
        
        if size:  
          current_size = os.path.getsize(filename)
          size_check =  current_size == size
          logger.debug("<{}>:{}::\"{}\" {}".format("upload_file:",filename,"Size Check",size_check))
        else:
          #If we did not get a size but did get a hash then we pass the check so the other one if the check
          size_check=not hash==None
        
      if  hash_check and size_check:
        return (True,"Cached")        

      url = self.project_URL+"files?parentId="+pathId

      logger.debug("<{}>:{}::\"{}\"".format("upload_file:","Upload Started",filename))
      files = {'file': open(filename, 'rb')}
      r = requests.post(url, files=files,cookies=self.cookies,headers=self.headers)
#      with open(filename, 'rb') as f:
#         requests.post(url, data=f,cookies=self.cookies,headers=self.headers)
      logger.debug("<{}>:{}::\"{}\"".format("upload_file:","Upload Finished",filename))
      return (True,"Uploaded")        
    else: 
      logger.info("<{}>:{}::\"{}\"".format("upload_file:","Not a file",filename))
      return (False,"Not_File")        

  def set_projects_area(self,area):
    params={
      "location":area,
      "fromDate":None,
      "toDate":None,
      "dateTypes":["Modified"]}
    
#    print "About to set region"
#    headers["Content-Type"]= "application/xml"


    r=requests.post(API_URL+"projects/filters", cookies=self.cookies,headers=self.headers,json=params)
    #This hack is because you need to talk to the correct connect server based on region, even though it is not documented at all.
    
    if area == "asia":
      self.project_URL=ASIA_API_URL
    elif area == "europe":
      self.project_URL=EUROPE_API_URL
    else: 
      self.project_URL=API_URL

    return(r.status_code==204)
  



  def logout(self):
# Logout is not in the V2 API
    r=requests.post("https://app.connect.trimble.com/tc/app/login/logout", cookies=self.cookies,headers=self.headers)

    return(r.status_code==200)

  def Login(self):

    self.session_token=None
    self.xsrf_token=None



    # We really should have a client ID assigned, this ID is the connect ID with that last letter changed from an a to A
    r = requests.get("https://identity.trimble.com/authorize/?client_id=TpMa5IZXttzRbryRkSkxiNuqNRAA&redirect_uri=https://app.connect.trimble.com/tc/app/oauth2/callback&response_type=code&scope=openid&state")
    logger.info("<{}>:\"{}\"".format(r.status_code,r.url))

    # When we get here we have been bounced multiple times, and have in the query string of the last URL the sessionDataKey which we need for the login


    URL=urlparse(r.url)
    parms=parse_qs(URL.query)
    sessionDataKey=parms["sessionDataKey"][0]
    logger.debug("sessionDataKey: \"{}\"".format(sessionDataKey))
#    pprint (r.headers)


    login_params={
      "user":self.user,
      "username" : self.user,
      "password" : self.password,
      "sessionDataKey" : sessionDataKey
      }

    #requests.post("http://identity.trimble.com/commonauth",data=login_params)
    #pprint (login_params)


    # The request that I shoudl have to make here should be simply
    # r=requests.post("https://identity.trimble.com/commonauth",data=login_params,allow_redirects=True)
    # But for some reason it doesn't work. It looks like the Cookie jar which needs to provide has commonAuthId 
    # doesn't work correctly over the redirects. Since requests doesn't allow me to break the SSL easily I am ignoreing this for now.


    r=requests.post("https://identity.trimble.com/commonauth",data=login_params,allow_redirects=False)
    logger.info("<{}>:\"{}\"".format(r.status_code,r.url))

    while  r.status_code == 301 or r.status_code==302 :
      r=requests.get(r.headers['location'],allow_redirects=False)
      logger.debug("<{}>:\"{}\"".format(r.status_code,r.url))
  #    print "Headers"
  #    pprint (r.headers)
  #    print "Cookies"
  #    pprint (r.cookies)
  #    print "Body"
  #    pprint (r.text)


    Logged_In=False
    if "s" in r.cookies:
      session_token=r.cookies["s"]
      xsrf_token=r.cookies["xsrf_token"]
      self.headers={"X-XSRF-Token": xsrf_token}
#                    "Content-Type": "application/json"}

      Logged_In=True
      logger.info("Logged in: Session : {} XSRF: {}".format(session_token,xsrf_token))
      self.cookies=dict(s=session_token,xsrf_token=xsrf_token)

    else:
      logger.warning("Failed to login")
  
    return (Logged_In)



if __name__ == "__main__":
  import sys  
  import datetime

  logging.basicConfig(level=logging.WARNING)

  
  print "Testing logging in as {}".format(sys.argv[1])
  Con=Connect(sys.argv[1],sys.argv[2])
  Logged_In = Con.Login()
  if Logged_In:
    print "Logged in as {}".format(sys.argv[1])
#    pprint (Con.cookies)
  else:
    print "Login failed"
    sys.exit(1)
    
  print "User Details"
#  pprint (Con.me())
  
  print "Regions"  
  pprint (Con.regions())
  

  print "Projects in Europe" 
  Con.set_projects_area("europe") 

  projects={}
  projects=Con.get_projects()
  
  for project_index in projects:
    project=projects[project_index]
    pprint (projects[project_index])
    print "{} {} ".format(project["name"],project["access"])
 
#Project Location doesn't report the location of the project :-(

  print "Projects in US"  
  Con.set_projects_area("us") 

  projects={}
  projects=Con.get_projects()
  pprint (projects)
  
  for project_index in projects:
    project=projects[project_index]
#    pprint (projects[project_index])
    print "{} {} {} {} {}".format(project["name"],project["access"],project["id"],project["foldersCount"],project["filesCount"])
 
 
#  print "Projects in Europe" 
#  Con.set_projects_area("europe") 
#  pprint (Con.projects())
  
#  TEST_PROJECT_ID="keiRTYOyDMM" # Trimble Building
#  TEST_PROJECT_ID="7E2ivKgwS5Q" # Dimensions
  
#  TEST_PROJECT_ID="VvXFRTbltU4" # Test Project

  TEST_PROJECT="TEST"
  TEST_PROJECT_ID=Con.get_project_by_name(TEST_PROJECT  )
  
#   pprint (TEST_PROJECT_ID)
  
#https://app.connect.trimble.com/tc/app/folders/children?parentId=dnQe85iHbhs&projectId=VvXFRTbltU4
  
#  TEST_ROOT_ID="QS19XFa8lRw"
    
  print "Test Project: " + TEST_PROJECT_ID 
  Con.set_projects_area("us") 
  project_info=Con.get_project_details(TEST_PROJECT_ID)
#  pprint (project_info)
#  pprint (Con.get_project_users(TEST_PROJECT_ID))
#  pprint (Con.get_project_roles(TEST_PROJECT_ID))
#  pprint (Con.get_project_settings(TEST_PROJECT_ID))

  root_id=Con.get_root_folder(project_info)  
#  folders=Con.get_folders(TEST_PROJECT_ID,root_id) 

  Con.upload_file(TEST_PROJECT_ID,root_id,"/Users/gkirk/GitHub/Connect/Connect_Lib/Test.py",None)

  folders=Con.get_children(root_id)
  
  print "Before Get Children Display "
  for folder_index in folders: #If the above is get_folders then any files in the root should be missed
    folder=folders[folder_index]
#    pprint (folder)
    if folder["type"] != "FOLDER":
      print "* {} {} {}".format(folder["name"], folder["type"], folder["size"],folder["revision"],folder["hidden"])
    else:
      print "  {} {} {}".format(folder["name"],folder["size"], folder["hasChildren"])
#      permissions = Con.get_folder_permissions(folder_index)
#      pprint (permissions)
      children= Con.get_children(folder_index)
      for child_index in children:
        child=children[child_index]
        if child["type"] != "FOLDER":
          print "**  {} {} {}".format(child["name"], child["type"], child["size"],child["revision"],child["hidden"])
        else:
          print "    {} {} {}".format(child["name"],child["size"], child["hasChildren"])

  print "After Get Children Display "

  files=Con.files_only(folders)
  print ""
  for file_index in files:
    file=files[file_index]
    print "{}:{} {} {}  {}".format(file["name"],file["revision"],file["size"],file["hash"], file["status"])

  folders=Con.folders_only(folders)
  print ""
  for folder_index in folders:
    folder=folders[folder_index]
#    pprint (folder)
    print "{}:{} {} {}".format(folder["name"],folder["size"],folder["hasChildren"], folder["versionId"])

    folderId=Con.get_folderId_by_path(TEST_PROJECT_ID,TEST_PROJECT,"/")
    pprint (folderId)

    folderId=Con.get_folderId_by_path(TEST_PROJECT_ID,TEST_PROJECT,"TEST_Folder")
    pprint (folderId)
#    pprint (file)
    
#    print ""
#    print "*Before Get Children*"
#    print "*Children*"
#    pprint (children)
#      print " **"
#      pprint (child)
#      print " **"
    
#https://app.connect.trimble.com/tc/app/folders/children?parentId=QS19XFa8lRw&projectId=keiRTYOyDMM    
#  pprint(folders)

# Building  projectId=keiRTYOyDMM
#https://app.connect.trimble.com/tc/app/folders?parentId=QS19XFa8lRw&projectId=keiRTYOyDMM

#https://app.connect.trimble.com/tc/app/folderPermissions/available?


  """
  todos =Con.get_todos(TEST_PROJECT_ID)
  
  for todo_index in todos:
#    pprint (todo)
#    pprint (todos[todo_index])
    todo=todos[todo_index]
    assigned_todo=""
    for assignee in todo["assignees"]:
      if assigned_todo != "":
        assigned_todo+=", "
      assigned_todo+= assignee["name"]
      
    print "{} : {} {} {} {} {}". format(todo["description"],todo["dueDate"],todo["createdBy"]["name"],todo["percentComplete"],assigned_todo,todo["startDate"])

    comments=Con.get_todo_comments(todo_index)
#    print "Comments"
#    pprint (comments)
    for comment_index in comments:
      comment = comments[comment_index]
#      pprint (comment)
      print  "*  "+comment['description']
      
#    https://app.connect.trimble.com/tc/app/comments?objectId=rLTZG_tO-q0&objectType=TODO&projectId=7E2ivKgwS5Q
"""

  (logged_in,details)=Con.me()
  if logged_in:
    print "Logged In"
  else:
    print "Logged out"
  
  print "Logging out"
  
  Con.logout()
  
  print "After logout: ", datetime.datetime.utcnow()

  (logged_in,details)=Con.me()
  if logged_in:
    print "Still Logged in"
  else:
    print "Logged Out"

  while logged_in:
    print datetime.datetime.utcnow(),
    print "User Details. "
#    print  details
    (logged_in,details)=Con.me()
    if logged_in:
      print "Still Logged in"
    else:
      print "Logged Out"
    
    
  
  
