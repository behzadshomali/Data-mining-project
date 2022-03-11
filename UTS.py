from cgi import print_exception
from BaseCrawler import BaseCrawler
import requests
from bs4 import BeautifulSoup
import logging
import os

logger = logging.getLogger('__main__')


class UTS(BaseCrawler):
    Course_Page_Url = "https://www.handbook.uts.edu.au/directory/courses.html"
    University = "University of Technology Sydney"
    Abbreviation = "UTS"
    University_Homepage = "https://www.uts.edu.au/"
    
    def get_courses_of_department(self, departmentLink):
        department_page_content = requests.get(departmentLink).text
        department_soup = BeautifulSoup(department_page_content, 'html.parser')

        Department_Name = department_soup.find(class_='ie-images').find('h1').text
        dirtyCoursesLinks = department_soup.find(class_='ie-images').find_all('a')
        coursesLinks = []
        for dirtyCourseLink in dirtyCoursesLinks:
            if dirtyCourseLink.text != '':
                if dirtyCourseLink.text[0].isdigit():
                    coursesLinks.append(dirtyCourseLink['href'])
        #print(coursesLinks)
        return coursesLinks, Department_Name

    def get_course_data(self, Course_Homepage):
        print(Course_Homepage)
        Projects = [] #Done
        Scores = None #Done
        Prerequisite = [] #Done
        Objective = [] #Done
        Description = None #Done
        Course_Title = None #Done
        Department_Name = None #Done
        Outcome = [] #Done
        References = [] #Done
        
        # Below fields can't be found on the website
        Professor = None
        Professor_Homepage = None
        Required_Skills = []
        
        course_page_content = requests.get(Course_Homepage).text
        course_soup = BeautifulSoup(course_page_content, 'html.parser')
        
        #Reaching detailed subject (course) homepage
        detailed_Course_Homepage = None
        Course_Homepage_a_elements = course_soup.find(class_="ie-images").find_all('a')
        for Course_Homepage_a_element in Course_Homepage_a_elements:
            if Course_Homepage_a_element.text == 'Detailed subject description.':
                detailed_course_relational_URL = Course_Homepage_a_element['href']
                detailed_Course_Homepage = self.relationalToAbsoluteAddress(Course_Homepage, detailed_course_relational_URL)

        if detailed_Course_Homepage is None:
            Unit_Count = course_soup.find(class_="ie-images").find('em').text[:-2]
        else:
            detailed_course_page_content = requests.get(detailed_Course_Homepage).text
            detailed_course_soup = BeautifulSoup(detailed_course_page_content, 'html.parser')
            detailed_course_ieImagesClass_elements = detailed_course_soup.find(class_="ie-images")

            #Finding Course Title
            Course_Title = self.listToString(detailed_course_ieImagesClass_elements.find('h1').text.split(' ')[1:], ' ')

            #Extracting useful em elements
            detailed_course_em_elements = detailed_course_ieImagesClass_elements.find_all('em')
            detailed_course_em_0_text = detailed_course_em_elements[0].text
            detailed_course_em_1 = detailed_course_em_elements[1]

            #Finding Department Name
            if detailed_course_em_0_text.count(':') == 2:
                Department_Name = detailed_course_em_0_text.split(':')[2][1:]
            elif detailed_course_em_0_text.count(':') == 1:
                Department_Name = detailed_course_em_0_text.split(':')[1][1:] + ' (Faculty)'
            else:
                Department_Name = None

            #Finding Unit Count
            Unit_Count = detailed_course_em_1.next_sibling.split(' ')[1]

            #Finding subject (course) Prerequisites
            if detailed_course_ieImagesClass_elements.find('a',text='access conditions') is not None:
                course_prerequisite_page_content = requests.get(detailed_course_ieImagesClass_elements.find('a',text='access conditions')['href']).text
                course_prerequisite_soup = BeautifulSoup(course_prerequisite_page_content, 'html.parser')
                course_prerequisite_table_rows = course_prerequisite_soup.find('table', cellpadding="2", width="650").find_all('tr')[2:]
                
                for course_prerequisite_table_row in course_prerequisite_table_rows:
                    course_prerequisite_table_row_data_list = course_prerequisite_table_row.find_all('td')
                    if course_prerequisite_table_row_data_list[1].text == 'Academic requisite':
                        Prerequisite.append(self.listToString(course_prerequisite_table_row_data_list[2].text.split(' ')[1:], ' '))

            #Finding subject (course) Description
            #if detailed_course_ieImagesClass_elements.find('h3', text= 'Description') is not None:
            Description = detailed_course_ieImagesClass_elements.find('h3', text= 'Description').next_element.next_element.next_element.find('p').text[1:]

            #Finding subject (course) Objectives
            if detailed_course_ieImagesClass_elements.find('table', class_='SLOTable') is not None:
                course_objectives_td_elements = detailed_course_ieImagesClass_elements.find('table', class_='SLOTable').find_all('td')
                for course_objective_td_element in course_objectives_td_elements:
                    Objective.append(course_objective_td_element.text)

            #Finding subject (course) Outcomes
            if detailed_course_ieImagesClass_elements.find('ul', class_='CILOList') is not None:
                course_outcomes_li_elements = detailed_course_ieImagesClass_elements.find('ul', class_='CILOList').find_all('li')
                for course_outcome_li_element in course_outcomes_li_elements:
                    Outcome.append(course_outcome_li_element.text)

            #Finding subject (course) Projects
            if detailed_course_ieImagesClass_elements.find_all('table', class_='assessmentTaskTable') is not None:
                course_assessments_tables = detailed_course_ieImagesClass_elements.find_all('table', class_='assessmentTaskTable')
                for course_assessment_table in course_assessments_tables:
                    project_description = None
                    course_assessment_table_tr_elements = course_assessment_table.find_all('tr')
                    for course_assessment_table_tr_element in course_assessment_table_tr_elements:
                        course_assessment_table_tr_th_element = course_assessment_table_tr_element.find('th', class_='assessmentTaskTableMainHeading')
                        if course_assessment_table_tr_th_element is not None:
                            course_assessment_table_tr_th_element_text = course_assessment_table_tr_th_element.text
                            if course_assessment_table_tr_th_element_text == 'Intent:':
                                if course_assessment_table_tr_element.find('td').find('p') is not None: 
                                    project_description = course_assessment_table_tr_element.find('td').find('p').text
                                else:
                                    project_description = course_assessment_table_tr_element.find('td').text
                            
                            elif course_assessment_table_tr_th_element_text == 'Type:':
                                if course_assessment_table_tr_element.find('td').find('p') is not None: 
                                    assessment_type = course_assessment_table_tr_element.find('td').find('p').text
                                else:
                                    assessment_type = course_assessment_table_tr_element.find('td').text
                                
                                if assessment_type == 'Project' and project_description is not None:
                                    Projects.append(project_description)
                                    break

            #Finding subject (course) Scores
            if detailed_course_ieImagesClass_elements.find('em') is not None:
                for detailed_course_em_element in detailed_course_em_elements:
                    if detailed_course_em_element.text == 'Result type':
                        Scores = detailed_course_em_element.next_sibling.text.split(':')[1].strip()
                        break

            #Finding subject (course) References
            if detailed_course_ieImagesClass_elements.find_all('h3') is not None:
                for detailed_course_h3_element in detailed_course_ieImagesClass_elements.find_all('h3'):
                    if detailed_course_h3_element.text == 'References':
                        element = detailed_course_h3_element
                        while element.next_element is not None:
                            if element.next_element.text.strip() != '':
                                if element.next_element.text.strip() != 'References':
                                    References.append(element.next_element.text.strip())
                            element = element.next_element
                        break

        return Course_Title, Department_Name, Unit_Count, Description, Objective, Professor, Required_Skills, Outcome, Scores, Prerequisite, Projects, Professor, Professor_Homepage, References

    def handler(self):
        #Reaching subjects (courses) URL
        html_content = requests.get(self.Course_Page_Url).text
        soup = BeautifulSoup(html_content, 'html.parser')

        sidebar_links = soup.find(id="sectionGroup15101").find_all('li')
        for sidebar_link in sidebar_links:
            if 'subjects' in sidebar_link.find('a')['href']:
                subjects_page_URL = sidebar_link.find('a')['href']
                if subjects_page_URL.endswith('index.html'):
                    subjects_page_URL = subjects_page_URL[0:len(subjects_page_URL) - 10]
        # print(subjects_page_URL)
        
        #Reaching Numerical list of subjects (courses) URL
        subjects_page_content = requests.get(subjects_page_URL).text
        subjects_page_soup = BeautifulSoup(subjects_page_content, 'html.parser')

        subjects_lists_URLs = subjects_page_soup.find(class_="toc").find_all('a')
        for  subjects_list_URL in subjects_lists_URLs:
            if 'numerical' in subjects_list_URL['href']:
                if subjects_list_URL['href'].endswith('index.html'):
                    numerical_subjects_list_URL = subjects_page_URL + subjects_list_URL['href'][0:len(subjects_list_URL) - 10]
                else:
                    numerical_subjects_list_URL = subjects_page_URL + subjects_list_URL['href']
        
        numerical_subjects_list_content = requests.get(numerical_subjects_list_URL).text
        numerical_subjects_list_soup = BeautifulSoup(numerical_subjects_list_content, 'html.parser')

        #Extracting each subject (course) URL and getting its data
        courses_a_elements = numerical_subjects_list_soup.find(class_='ie-images').find_all('a')
        Courses_Homepages = []
        for course_a_element in courses_a_elements:
            if course_a_element.text[0].isdigit():
                Courses_Homepages.append(course_a_element['href'])
        #print(Courses_Homepages)

        print('0 / ' + str(len(Courses_Homepages)))

        for i in range(len(Courses_Homepages)):
            Course_Homepage = Courses_Homepages[i]
            Course_Title, Department_Name, Unit_Count, Description, Objective, Professor, Required_Skills, Outcome, Scores, Prerequisite, Projects, Professor, Professor_Homepage, References = self.get_course_data(Courses_Homepages[i])
            if (i + 1) % 20 == 0:
                print(str(i + 1) + ' / ' + str(len(Courses_Homepages)))

            self.save_course_data(
                self.University, self.Abbreviation, Department_Name, Course_Title, Unit_Count,
                Professor, Objective, Prerequisite, Required_Skills, Outcome, References, Scores,
                Description, Projects, self.University_Homepage, Course_Homepage, Professor_Homepage
            )

        logger.info(f"{self.Abbreviation}: {Department_Name} department's data was crawled successfully.")

        logger.info(f"{self.Abbreviation}: Total {self.course_count} courses were crawled successfully.")
    
    def relationalToAbsoluteAddress(self, currentDirectory, relationalAddress):
        relativePart = relationalAddress.split('/')[0]
        for i in range(len(relativePart)):
            if relativePart[i] == '.':
                if i == 0:
                    leftPart = self.listToString(currentDirectory.split('/')[:len(currentDirectory.split('/')) - 1], '/')
                else:
                    leftPart = self.listToString(leftPart.split('/')[:len(leftPart.split('/')) - 1], '/')
            else:
                print('Wrong Relational Address!')
            absoluteAddress = leftPart + '/' + self.listToString(relationalAddress.split('/')[1:], '/')
        return absoluteAddress
    
    def listToString(self, ls, separator):
        string = ''
        for element in ls:
            if string == '':
                string += element
            else:
                string += separator + element
        return string
            

if __name__ == "__main__":       
    if 'data' not in os.listdir():
        os.mkdir('data')

    uts = UTS()