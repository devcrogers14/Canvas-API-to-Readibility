#A Program that takes the user's API key and retrives the information associated with it
import os
import dotenv import load_dotenv
from wsgiref import headers
from urllib.request import Request, urlopen
import json


#Tell the program which instructure to take the info from
canvas_url = "https://iit.instructure.com/api/v1"
load_dotenv()  # Load environment variables from .env file
apiKey = os.getenv("CANVAS_API_KEY")


class Course:

    def __init__(self, course_id, course_name, course_code):
        self.course_id = course_id
        self.course_name = course_name
        self.course_code = course_code
        
    def courseInfo(self):
        return f"Course ID: {self.course_id}, Course Name: {self.course_name}, Course Code: {self.course_code}"

    @classmethod
    def getCourses(cls):
        #Declare an endpoint to the request which is the user's profile info
        coursesEnd = f"{canvas_url}/courses?include[]=course"
        
        #This header must be used otherwise canvas will not accept the request
        headers = {
        "Authorization": f"Bearer {apiKey}"
        }
        
        #Make the request to the Canvas API and save the response
        request = Request(coursesEnd, headers=headers)
        response = urlopen(request)
        
        courses = []
        if response.status == 200: #200 meaning the request was successful
            data = json.loads(response.read())
            for course_data in data:
                if course_data.get("workflow_state") == "available":
                    course_id = course_data.get("id")
                    course_name = course_data.get("name")
                    course_code = course_data.get("course_code")
                    courses.append(cls(course_id, course_name, course_code))
            print("Courses retrieved successfully: \n")
        return courses

    def getAssignments(self, course_id):
        assignmentsEnd = f"{canvas_url}/courses/{course_id}/assignments"
        headers = {
            "Authorization": f"Bearer {apiKey}"
        }
        for course in self.getCourses():
            course.course_id = course_id
            assignmentsRequest = Request (assignmentsEnd, headers=headers)
            

def main():
    courses = Course.getCourses()
    for course in courses:
        print(course.courseInfo())


if __name__ == "__main__":
    main()