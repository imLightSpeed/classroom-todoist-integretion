from __future__ import print_function
import pickle
import os
import os.path
import requests
import pytz
import time
import zulu
import datetime,pprint
from todoist.api import TodoistAPI
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
while True:
    list_assigments =[]
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly','https://www.googleapis.com/auth/classroom.student-submissions.me.readonly','https://www.googleapis.com/auth/classroom.push-notifications']
    def main():
        """Shows basic usage of the Classroom API.
        Prints the names of the first 10 courses the user has access to.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('classroom', 'v1', credentials=creds)

        # Call the Classroom API
        courses = []
        page_token = None

        while True:
            response = service.courses().list(pageToken=page_token,
                                            pageSize=10,courseStates= ["ACTIVE"]).execute()
            courses.extend(response.get('courses', []))
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break
        list_courses=[]
        if not courses:
            raise
        else: 
            for course in courses:
                list_courses.append(course.get('id'))
            for x in list_courses:
                if not service.courses().courseWork().list(courseId=x).execute() == {}:
                    response = service.courses().courseWork().list(courseId=x).execute()
                    list_dict = response['courseWork']
                    for count, item in enumerate(list_dict):
                        assigment_info = list_dict[count]
                        assignment_id = assigment_info['id']
                        state = service.courses().courseWork().studentSubmissions().list(courseId=x, courseWorkId=assignment_id).execute()
                        sub_list_dict = state['studentSubmissions']
                        student_list = sub_list_dict[0]

                        local_tz = pytz.timezone('US/Eastern')
                        try:
                            date = assigment_info['dueDate']
                            time = assigment_info['dueTime']
                            is_due_date = True
                        except KeyError:
                            is_due_date = False
                        if is_due_date:
                            try:
                                due_date = datetime.datetime(date['year'],date['month'],date['day'],time['hours'],time['minutes'])
                            except KeyError:
                                due_date = datetime.datetime(date['year'],date['month'],date['day'],time['hours'])
                            local_dt = due_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                            local_dt =local_tz.normalize(local_dt)
                            format_time = local_dt.strftime('%m/%d/%Y %H:%M')
                        else:
                            format_time = None
                        title =assigment_info['title']
                        courseId=assigment_info['courseId']
                        info = []
                        info.append(assigment_info['title'])
                        info.append(assigment_info['courseId'])
                        info.append(format_time)
                        update =assigment_info['updateTime']
                        last_updated = zulu.parse(update)
                        last_updated =last_updated.naive
                        ulocal_dt = last_updated.replace(tzinfo=pytz.utc).astimezone(local_tz)
                        ulocal_dt =local_tz.normalize(ulocal_dt).strftime('%m/%d/%Y %H:%M')
                        info.append(ulocal_dt)
                        info.append(student_list['state'])
                        list_assigments.append(info)
        return list_assigments
                
            
    token = os.environ.get('TODOIST_TOKEN')

    class todoist:
        """Connects to todoist and then makes a post request for tast - pass in name, project and due date.
        """    
        def __init__(self, task, project,date):
            super().__init__()
            self.task=task
            self.project=project
            self.date=date
            api = TodoistAPI(token)
            api.add_item(self.task, project_id=self.project,date_string=self.date )
            api.commit() 
                
        
    if __name__ == '__main__':
        main()
        current = datetime.datetime.now()

        if not os.path.exists('lastrun.txt'):
            file = open("lastrun.txt", "w+")
            file.write(current.strftime('%m/%d/%Y %H:%M'))
            file.close()
        
        file = open("lastrun.txt", "r+")
        file_time= file.readlines()
        file_time = datetime.datetime.strptime(file_time[0], '%m/%d/%Y %H:%M')
        file.seek(0)
        file.truncate()
        file.write(current.strftime('%m/%d/%Y %H:%M'))
        for item in list_assigments:
            update_date = datetime.datetime.strptime(item[3], '%m/%d/%Y %H:%M')
            #print(update_date,file_time)
            
            #if item[0].find('Attendence') != -1 and len(item) == 3:
                #item.insert(2,'today')
            if update_date>file_time and item[-1]!= 'TURNED_IN':
                class_id = item[1]
                classes ={
                    '153411592343':2243124289,
                    '153357455054':2243124161,
                    '153401264150':2243124368,
                    '158148170837':243465271,
                    '152361476207':2243465241,
                    '153384958450':2243124172,
                    '152983425904':2243124200,
                    '152983509662':2243124132,
                    '153477712957':2243464933
                }

                todoist(item[0],classes[class_id], item[2])
                print(f'Task: {item[0]} added for {classes[class_id]}. It is due {item[2]}')
            else:
                pass
                
        file.close()
    time.sleep(360)

