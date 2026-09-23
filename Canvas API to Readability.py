import datetime
import json
import os
from urllib.request import Request, urlopen

# Setup details for Canvas
canvas_url = "https://iit.instructure.com/api/v1"
apiKey = os.getenv("CANVAS_API_KEY")

# Get today's date in the format Canvas uses (Year-Month-Day)
today = datetime.datetime.now().strftime("%Y-%m-%d")


class Course:

    def __init__(self, course_id, course_name, course_code):
        self.course_id = course_id
        self.course_name = course_name
        self.course_code = course_code
        self.assignments = []  # Starts empty for every new course

    def courseInfo(self):
        return f"Course ID: {self.course_id} | Name: {self.course_name} ({self.course_code})"

    @classmethod
    def getCourses(cls):
        courses_endpoint = f"{canvas_url}/courses?include[]=course"
        headers = {"Authorization": f"Bearer {apiKey}"}

        request = Request(courses_endpoint, headers=headers)
        response = urlopen(request)

        course_list = []
        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))
            for course_data in data:
                if course_data.get("workflow_state") == "available":
                    new_course = cls(
                        course_id=course_data.get("id"),
                        course_name=course_data.get("name"),
                        course_code=course_data.get("course_code"),
                    )
                    course_list.append(new_course)

        return course_list

    def getAssignments(self):
        # Look up assignments using this specific course's ID
        assignments_endpoint = (
            f"{canvas_url}/courses/{self.course_id}/assignments"
        )
        headers = {"Authorization": f"Bearer {apiKey}"}

        request = Request(assignments_endpoint, headers=headers)
        response = urlopen(request)

        self.assignments = []  # Clear out any old assignments

        if response.status == 200: #Checks for a successful response
            data = json.loads(response.read().decode("utf-8"))
            for item in data:
                due_date = item.get("due_at")
                assignment_name = item.get("name")

                # If it has a deadline and that deadline is in the future
                if due_date and due_date > today:
                    self.assignments.append(
                        {"name": assignment_name, "due_date": due_date}
                    )
        else:
            print(f"Failed to retrieve assignments for {self.course_name}. Status code: {response.status}")

        return self.assignments

    def printAssignments(self):
        print(f"\nAssignments for {self.course_name}:")

        # Check if the list has anything inside it
        if len(self.assignments) == 0:
            print("  No upcoming assignments found.")
        else:
            for assignment in self.assignments:
                print(
                    f"  - {assignment['name']} (Due: {assignment['due_date']})"
                )


def main():
    all_courses = Course.getCourses()

    #handles all logic for nicely formatting user schedules and assignments
    print("--- Available Courses ---")
    for course in all_courses:
        print(course.courseInfo())
    print("\n" + "=" * 40)




    while True:
        user_choice = input(
            "Enter a Course ID, press Enter for all, or type 'exit': "
        ).strip()

        if user_choice.lower() == "exit":
            print("Exiting program.")
            break

        # OPTION 1: User pressed Enter -> show every course
        elif user_choice == "":
            for course in all_courses:
                course.getAssignments()
                course.printAssignments()

        # OPTION 2: User entered a specific course ID
        else:
            found_course = False

            # Look through all our courses to find the matching one
            for course in all_courses:
                if str(course.course_id) == user_choice:
                    course.getAssignments()
                    course.printAssignments()
                    found_course = True

            if not found_course:
                print(f"Could not find any course with ID: {user_choice}")
                continue


if __name__ == "__main__":
    main()