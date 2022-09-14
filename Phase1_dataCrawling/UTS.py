from cgi import print_exception
from BaseCrawler import BaseCrawler
import requests
from bs4 import BeautifulSoup
import logging
import os
from math import ceil
import time
from time import sleep
from threading import Thread
from random import randint

logger = logging.getLogger('__main__')
threads_count = 12

def chunks(list, n):
    '''Split the input list into n seperated lists'''
    step_size = int(ceil(len(list) / n))
    for i in range(0, len(list), step_size):
        yield list[i:i + step_size]


def random_IP_generator():
    '''Generate a random IP address'''
    return "{}.{}.{}.{}".format(randint(100,255),randint(0,255),randint(0,255),randint(0,255))


class UTS(BaseCrawler):
    Course_Page_Url = "https://www.handbook.uts.edu.au/directory/courses.html"
    University = "University of Technology Sydney"
    Abbreviation = "UTS"
    University_Homepage = "https://www.uts.edu.au/"
    
    def get_courses_of_department(self, departmentLink):
        headers = {"X-Forwarded-For": random_IP_generator()}
        department_page_content = requests.get(departmentLink, headers=headers, timeout=6).text
        department_soup = BeautifulSoup(department_page_content, 'html.parser')

        Department_Name = department_soup.find(class_='ie-images').find('h1').text
        dirtyCoursesLinks = department_soup.find(class_='ie-images').find_all('a')
        coursesLinks = []
        for dirtyCourseLink in dirtyCoursesLinks:
            if dirtyCourseLink.text != '':
                if dirtyCourseLink.text[0].isdigit():
                    coursesLinks.append(dirtyCourseLink['href'])

        return coursesLinks, Department_Name

    def get_course_data(self, Course_Homepage):
        Projects = [] 
        Scores = None 
        Prerequisite = [] 
        Objective = [] 
        Description = None 
        Course_Title = None 
        Department_Name = None 
        Outcome = [] 
        References = [] 
        
        # Below fields can't be found on the university's website
        Professor = None
        Professor_Homepage = None
        Required_Skills = []
        
        try:
            headers = {"X-Forwarded-For": random_IP_generator()}
            course_page_content = requests.get(Course_Homepage, headers=headers, timeout=6).text
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
                detailed_course_page_content = requests.get(detailed_Course_Homepage, headers=headers, timeout=6).text
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
                    course_prerequisite_page_content = requests.get(detailed_course_ieImagesClass_elements.find('a',text='access conditions')['href'], headers=headers, timeout=6).text
                    course_prerequisite_soup = BeautifulSoup(course_prerequisite_page_content, 'html.parser')

                    if course_prerequisite_soup.find('table', cellpadding="2", width="650") is not None:
                        course_prerequisite_table_rows = course_prerequisite_soup.find('table', cellpadding="2", width="650").find_all('tr')[2:]
                        
                        if course_prerequisite_table_rows is not None:
                            for course_prerequisite_table_row in course_prerequisite_table_rows:
                                course_prerequisite_table_row_data_list = course_prerequisite_table_row.find_all('td')
                                if course_prerequisite_table_row_data_list[1].text == 'Academic requisite':
                                    Prerequisite.append(self.listToString(course_prerequisite_table_row_data_list[2].text.split(' ')[1:], ' '))

                #Finding subject (course) Description
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
            
            corrupted_link = False
            return Course_Title, Department_Name, Unit_Count, Description, Objective, Professor, Required_Skills, Outcome, Scores, Prerequisite, Projects, Professor, Professor_Homepage, References, Course_Homepage, corrupted_link
        except Exception as e:
            corrupted_link = True
            print(e)
            return corrupted_link

    def get_course_data_thread(self, Courses_Homepages, data, thread_num, corrupted_links):
        for i in range(len(Courses_Homepages)):
            data.append(self.get_course_data(Courses_Homepages[i]))
            if data[-1] == True: # Link was broken
                data.pop()
                print(f'{thread_num} - {Courses_Homepages[i]} - Link was broken')
                corrupted_links.append(Courses_Homepages[i])

            if (i + 1) % 20 == 0:
                '''Printing the progress of the thread'''
                print(f'Thread {thread_num}: {i+1} / {len(Courses_Homepages)}')

        print(f'Thread {thread_num} finished!')

    def handler(self):
        #Reaching subjects (courses) URL
        headers = {"X-Forwarded-For": random_IP_generator()}
        html_content = requests.get(self.Course_Page_Url, headers=headers, timeout=6).text
        soup = BeautifulSoup(html_content, 'html.parser')

        if soup.find(id="sectionGroup15101") is not None:
            sidebar_links = soup.find(id="sectionGroup15101").find_all('li')
            for sidebar_link in sidebar_links:
                if 'subjects' in sidebar_link.find('a')['href']:
                    subjects_page_URL = sidebar_link.find('a')['href']
                    if subjects_page_URL.endswith('index.html'):
                        subjects_page_URL = subjects_page_URL[0:len(subjects_page_URL) - 10]
            
            #Reaching Numerical list of subjects (courses) URL
            subjects_page_content = requests.get(subjects_page_URL, headers=headers, timeout=6).text
            subjects_page_soup = BeautifulSoup(subjects_page_content, 'html.parser')

            subjects_lists_URLs = subjects_page_soup.find(class_="toc").find_all('a')
            for  subjects_list_URL in subjects_lists_URLs:
                if 'numerical' in subjects_list_URL['href']:
                    if subjects_list_URL['href'].endswith('index.html'):
                        numerical_subjects_list_URL = subjects_page_URL + subjects_list_URL['href'][0:len(subjects_list_URL) - 10]
                    else:
                        numerical_subjects_list_URL = subjects_page_URL + subjects_list_URL['href']
            
            numerical_subjects_list_content = requests.get(numerical_subjects_list_URL, headers=headers, timeout=6).text
            numerical_subjects_list_soup = BeautifulSoup(numerical_subjects_list_content, 'html.parser')

            #Extracting each subject (course) URL and getting its data
            courses_a_elements = numerical_subjects_list_soup.find(class_='ie-images').find_all('a')
            Courses_Homepages = []
            for course_a_element in courses_a_elements:
                if course_a_element.text[0].isdigit():
                    Courses_Homepages.append(course_a_element['href'])

            print('0 / ' + str(len(Courses_Homepages)))

            since = time.time()
            all_courses_data = []
            all_corrupted_links = []
            threads = []
            for i, course_humpages_sublist in enumerate(chunks(Courses_Homepages[::-1], threads_count)):
                print(f'Initializing thread {i+1}')
                data = []
                corrupted_links = []
                thread = Thread(target=self.get_course_data_thread, args=(course_humpages_sublist, data, i + 1, corrupted_links))
                threads.append(thread)
                all_courses_data.append(data)

            for i, thread in enumerate(threads):
                print(f'Starting thread {i+1}')
                thread.start()

            for thread in threads:
                thread.join()

            print(f'Sleep for 10 seconds')
            sleep(10)

            courses_data = []
            for corrupted_links in all_corrupted_links:
                for corrupted_link in corrupted_links:
                    courses_data.append(self.get_course_data(corrupted_link))
                    if courses_data[-1] == True:
                        courses_data.pop()
                        print(f'{corrupted_link} was broken!!')

            all_courses_data.append(courses_data)

            index = 1
            for courses_data in all_courses_data:
                for course_data in courses_data:
                    Course_Title, Department_Name, Unit_Count, Description, Objective, Professor, Required_Skills, Outcome, Scores, Prerequisite, Projects, Professor, Professor_Homepage, References, Course_Homepage, _ = course_data
                    self.save_course_data(
                        self.University, self.Abbreviation, Department_Name, Course_Title, Unit_Count,
                        Professor, Objective, Prerequisite, Required_Skills, Outcome, References, Scores,
                        Description, Projects, self.University_Homepage, Course_Homepage, Professor_Homepage
                    )
                    print(f'{index}/{Course_Title} saved!')
                    index += 1

            end = time.time()
            print(f'Time elapsed: {(end - since) / 60:.2f} minutes for crawling data!')
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