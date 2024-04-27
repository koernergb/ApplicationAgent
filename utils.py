import os
import openai
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.drive import GoogleDrive

def set_openai_api_key():
    print("Loading dotenv...")
    load_dotenv()
    print("Loading OpenAI API key...")
    openai.api_key = os.environ["OPENAI_API_KEY"]

def get_job_links_from_file(file_path):
    with open(file_path, 'r') as file:
        urls = file.read().splitlines()
    return urls

def make_gpt_api_call(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            n=1,
            stop=None,
            temperature=0.05,
        )
        print("Successful API call")
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error occurred during API call: {e}")
        return None

def fetch_job_posting_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job posting content from {url}: {e}")
        return None

def open_and_return_cover_letters():
    cover_letter_01 = ""
    cover_letter_02 = ""

    with open("./sample_cover_letter_01.txt", "r") as file:
        cover_letter_01 = file.read()
    with open("./sample_cover_letter_02.txt", "r") as file:
        cover_letter_02 = file.read()

    print("Opened both cover letters\n" + cover_letter_01 + "\n" + cover_letter_02)
    return cover_letter_01, cover_letter_02

def write_cover_letter(cover_letter_01, cover_letter_02, company_name, job_posting_content):
    application_draft = make_gpt_api_call(
        f""" Here are two sample cover letters: \n {cover_letter_01} \n {cover_letter_02} \n 
        Write a new cover letter based on an adaptation of the content of the two sample cover letters to the following job posting: \n {job_posting_content} """
    )
    print(f"The application draft for {company_name} is: \n {application_draft}")
    return application_draft

def get_company_name(job_posting_content):
    company_name_prompt = f""" 
    What is the name of the company that made the following job posting? 
    Just give the name of the company in your response, no extra words. 
    Like for example: "Ford" "Google" "IMC" 
    Here is the job posting: {job_posting_content}"""
    company_name = make_gpt_api_call(company_name_prompt)
    print("API Call complete, the company is " + company_name)
    return company_name

def create_google_doc(cover_letter, company, folder_id, drive):
    file_metadata = {
        'title': f'{company} Cover Letter',
        'parents': [{'id': folder_id}],
        'mimeType': 'application/vnd.google-apps.document'
    }
    file_obj = drive.CreateFile(file_metadata)
    file_obj.SetContentString(cover_letter)
    file_obj.Upload()
    print(f'Google Docs link: https://docs.google.com/document/d/{file_obj.get("id")}/edit')
    

def list_folders_in_drive(drive):
    file_list = drive.ListFile({'q': "mimeType='application/vnd.google-apps.folder'"}).GetList()
    folders = [folder for folder in file_list if folder['mimeType'] == 'application/vnd.google-apps.folder']

    if folders:
        print("List of folders:")
        for folder in folders:
            print(f"Folder Name: {folder['title']}, Folder ID: {folder['id']}")
    else:
        print("No folders found.")

def get_id_of_title(title, parent_directory_id, drive):
    file_list = drive.ListFile({'q': f"'{parent_directory_id}' in parents and trashed=false"}).GetList()
    for file in file_list:
        if file['title'] == title:
            return file['id']
    return None


def get_job_duties(job_posting_content):
    duties_prompt = f"""
    What are the duties or responsibilities listed in this job posting?
    What work will the job entail?
    Please answer as a bulleted list of duties, one per line.
    Here is the job posting: {job_posting_content}
    """
    duties = make_gpt_api_call(duties_prompt)
    print("API Call complete, the duties are " + duties)
    return duties

def get_job_requirements(job_posting_content):
    requirements_prompt = f"""
    What are the requirements listed in this job posting?
    What experience or skills will the applicant need to have?
    Please answer as a bulleted list of requirements, one per line.
    Here is the job posting: {job_posting_content}
    """
    requirements = make_gpt_api_call(requirements_prompt)
    print("API Call complete, the requirements are " + requirements)
    return requirements



