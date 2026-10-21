import datetime
import json
import os
import secrets
from pathlib import Path
from urllib.request import Request, urlopen
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import TokenVerifier, AccessToken

# Load keys from the .env beside this script, even when launched from another folder.
# Existing environment variables take priority over values in the file.
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

# Setup details for Canvas
canvasUrl = "https://iit.instructure.com/api/v1"
canvasApiKey = os.getenv("CANVAS_API_KEY")

# This is the separate secret that Lucas needs before he can use our server.
serverAccessToken = os.getenv("MCP_SERVER_TOKEN", "").strip()

# Stop here if the secret is missing or too short so we do not run an open server.
if len(serverAccessToken) < 32:
    raise ValueError("Add a randomly generated MCP_SERVER_TOKEN of at least 32 characters to .env, then restart the server.")


class ServerTokenChecker(TokenVerifier):
    # FastMCP calls this when someone sends a token with their request.
    # token is the value they sent, and serverAccessToken is the secret we saved.
    async def verify_token(self, token: str) -> AccessToken | None:
        # Compare the two secrets without giving away which characters matched.
        tokensMatch = secrets.compare_digest(
            token.encode("utf-8"),
            serverAccessToken.encode("utf-8"),
        )

        # Wrong token -> tell FastMCP to reject this request.
        if not tokensMatch:
            return None

        # Correct token -> let this request use our MCP tools.
        # lucas is just a label. Anyone who has this secret can use it.
        return AccessToken(token=token, client_id="lucas", scopes=[])


mcp = FastMCP(
    name="Canvas Readability",
    instructions="A tool to read Canvas assignments and grades",
    version="1.0.0",
    # This actually turns on the token check for incoming MCP requests.
    auth=ServerTokenChecker(),
)


def canvas_headers():
    # Validate only when a Canvas tool is called, so other integrations can still run.
    if not canvasApiKey or not canvasApiKey.strip():
        raise ValueError("Add CANVAS_API_KEY to the .env beside this script, save it, and restart the server.")
    return {"Authorization": f"Bearer {canvasApiKey.strip()}"}


# Get the current week from Monday through Sunday.
currentDate = datetime.date.today()
weekStart = currentDate - datetime.timedelta(days=currentDate.weekday())
weekEnd = weekStart + datetime.timedelta(days=6)


class Assignment:

    def __init__(self, name, dueDate, submitted, score=None):
        self.name = name
        self.dueDate = dueDate
        self.submitted = submitted
        self.score = score


class Course:

    def __init__(self, courseId, courseName, courseCode, grade=None):
        self.courseId = courseId
        self.courseName = courseName    
        self.courseCode = courseCode
        self.grade = grade
        self.assignments = []  # Starts empty for every new course

    def courseInfo(self):
        grade_info = f" | Grade: {self.grade}" if self.grade is not None else ""
        return f"Course ID: {self.courseId} | Name: {self.courseName} ({self.courseCode}){grade_info}"

    @classmethod
    def getCourses(cls):
        coursesEndpoint = f"{canvasUrl}/courses?include[]=course,total_scores&enrollment_state=active"
        headers = canvas_headers()

        request = Request(coursesEndpoint, headers=headers)
        response = urlopen(request)

        courseList = []
        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))
            for courseData in data:
                if courseData.get("workflow_state") == "available":
                    newCourse = cls(
                        courseId=courseData.get("id"),
                        courseName=courseData.get("name"),
                        courseCode=courseData.get("course_code"),
                        grade=courseData.get("total_scores", {}).get("current_score")
                    )
                    courseList.append(newCourse)

        return courseList
    def getAssignments(self):
        # Look up assignments using this specific course's ID
        assignmentsEndpoint = (
            f"{canvasUrl}/courses/{self.courseId}/assignments?include[]=submission"
        )
        headers = canvas_headers()

        request = Request(assignmentsEndpoint, headers=headers)
        response = urlopen(request)

        self.assignments = []  # Clear out any old assignments

        if response.status == 200: #Checks for a successful response
            data = json.loads(response.read().decode("utf-8"))
            for item in data:
                dueDate = item.get("due_at")
                assignmentName = item.get("name")
                submission = item.get("submission") or {}
                submitted = submission.get("submitted_at") is not None
                score = submission.get("score")

                if dueDate:
                    dueDateValue = datetime.datetime.fromisoformat(
                        dueDate.replace("Z", "+00:00")
                    ).date()

                # Include assignments due this week, whether submitted or not.
                if dueDate and weekStart <= dueDateValue <= weekEnd:
                    self.assignments.append(
                        Assignment(
                            name=assignmentName,
                            dueDate=dueDate,
                            submitted=submitted,
                            score=score,
                        )
                    )
        else:
            print(f"Failed to retrieve assignments for {self.courseName}. Status code: {response.status}")

        return self.assignments

    def printAssignments(self):
        print(f"\nAssignments for {self.courseName}:")

        # Check if the list has anything inside it
        if len(self.assignments) == 0:
            print("  No assignments due this week found.")
        else:
            for assignment in self.assignments:
                print(
                    f"  - {assignment.name} (Due: {assignment.dueDate}) "
                    f"[Submitted: {assignment.submitted}] "
                    f"[Score: {assignment.score if assignment.score is not None else 'N/A'}]"
                )


# Lucas calls these tools with simple arguments; the classes organize data internally.
@mcp.tool
def get_courses() -> list[dict]:
    """List available Canvas courses and their IDs."""
    return [
        {"course_id": c.courseId, "name": c.courseName,
         "course_code": c.courseCode, "grade": c.grade}
        for c in Course.getCourses()
    ]


@mcp.tool
def check_modules(course_id: int) -> list[dict]:
    """List course modules and their items for a positive Canvas course ID."""
    if course_id <= 0:
        raise ValueError("Use a positive Canvas course ID.")

    courseModulesEndpoint = f"{canvasUrl}/courses/{course_id}/modules?include[]=items"
    canvasRequest = Request(courseModulesEndpoint, headers=canvas_headers())
    with urlopen(canvasRequest) as canvasResponse:
        return json.loads(canvasResponse.read().decode("utf-8"))


@mcp.tool
def get_assignments(course_id: int) -> list[dict]:
    """Get assignments due this week for a course ID returned by get_courses."""
    if course_id <= 0:
        raise ValueError("Use a positive Canvas course ID.")
    course = Course(course_id, "", "")
    return [
        {"name": a.name, "due_date": a.dueDate,
         "submitted": a.submitted, "score": a.score}
        for a in course.getAssignments()
    ]


def main():
    allCourses = Course.getCourses()

    #handles all logic for nicely formatting user schedules and assignments
    print("--- Available Courses ---")
    for course in allCourses:
        print(course.courseInfo())
    print("\n" + "=" * 40)


    while True:
        userChoice = input(
            "Enter a Course ID, press Enter for all, or type 'exit': "
        ).strip()

        if userChoice.lower() == "exit":
            print("Exiting program.")
            break

        # OPTION 1: User pressed Enter -> show every course
        elif userChoice == "":
            for courseIndex, course in enumerate(allCourses):
                course.getAssignments()
                course.printAssignments()

                if courseIndex < len(allCourses) - 1:
                    input("Press Enter to continue to the next course...")

        # OPTION 2: User entered a specific course ID
        else:
            foundCourse = False

            # Look through all our courses to find the matching one
            for course in allCourses:
                if str(course.courseId) == userChoice:
                    course.getAssignments()
                    course.printAssignments()
                    foundCourse = True

            if not foundCourse:
                print(f"Could not find any course with ID: {userChoice}")
                continue

# Listen locally on port 8000. Return JSON and handle each MCP request independently.
if __name__ == "__main__":
    mcp.run(
        transport= "http",
        host = "127.0.0.1",
        port = 8000,
        json_response = True,
        stateless_http = True,
    )