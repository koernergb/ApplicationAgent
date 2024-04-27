import os
import cohere
from dotenv import load_dotenv
from langchain import OpenAI, PromptTemplate
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

DEBUG = True

def set_cohere_api_key():
    load_dotenv()
    api_key = os.environ["COHERE_API_KEY"]
    if DEBUG:
        print("Opened and set Cohere API key")
    co = cohere.Client(api_key)
    return co

def set_openai_api_key():
    load_dotenv()
    openai_api_key = os.environ["OPENAI_API_KEY"]
    if DEBUG:
        print("Opened and set API key")
    return OpenAI(temperature=0.05, max_tokens=600, openai_api_key=openai_api_key)

def get_job_links_from_file(file_path):
    with open(file_path, 'r') as file:
        urls = file.read().splitlines()
    if DEBUG:
        print("Loaded job links from file")
    return urls

def fetch_job_posting_content(url):
    if (url==""):
        print("Empty URL")
        return "No posting content"
    loader = WebBaseLoader(url)
    data = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(data)
    result = ' '.join([doc.page_content for doc in docs])
    if DEBUG:
        print(f"RESULT: \n {result}")
    return result

def open_and_return_cover_letters():
    with open("./sample_cover_letter_01.txt", "r") as file:
        cover_letter_01 = file.read()
    with open("./sample_cover_letter_02.txt", "r") as file:
        cover_letter_02 = file.read()
    if DEBUG:
        print("Loaded cover letters from files")
    return cover_letter_01, cover_letter_02

def get_company_name(job_posting_content, co):
    company_name_template = f"""What is the name of the company that made the following job posting? Just give the name of the company in your response, no extra words. Like for example: "Ford" "Google" "IMC". Here is the job posting: {job_posting_content}"""
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=company_name_template,
        max_tokens=10,
        temperature=0.5,
        stop_sequences=[],
    )
    company_name = response.generations[0].text.strip()
    if DEBUG:
        print(f"Company Name: \n{company_name}")
    return company_name

def get_job_duties(job_posting_content, co):
    duties_template = f"""What are the duties or responsibilities listed in this job posting? What work will the job entail? Please answer as a bulleted list of duties, one per line. Here is the job posting: {job_posting_content}"""
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=duties_template,
        max_tokens=200,
        temperature=0.5,
        stop_sequences=[],
    )
    duties = response.generations[0].text.strip()
    if DEBUG:
        print(f"Duties: \n{duties}")
    return duties

def get_job_requirements(job_posting_content, co):
    requirements_template = f"""What are the requirements listed in this job posting? What experience or skills will the applicant need to have? Please answer as a bulleted list of requirements, one per line. Here is the job posting: {job_posting_content}"""
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=requirements_template,
        max_tokens=200,
        temperature=0.5,
        stop_sequences=[],
    )
    requirements = response.generations[0].text.strip()
    if DEBUG:
        print(f"Requirements: \n{requirements}")
    return requirements

def write_cover_letter(cover_letter_01, cover_letter_02, company_name, job_posting_content, resume, previous_cover_letters, co):
    # Limit the number of previous cover letters to include
    max_previous_cover_letters = 3
    previous_cover_letters = previous_cover_letters[-max_previous_cover_letters:]

    # Truncate the length of each previous cover letter
    max_cover_letter_length = 1000
    truncated_previous_cover_letters = [
        cover_letter[:max_cover_letter_length] for cover_letter in previous_cover_letters
    ]

    cover_letter_template = f"""Here are two sample cover letters:
    Cover Letter 1: {cover_letter_01}
    Cover Letter 2: {cover_letter_02}
    Here is the applicant's resume: {resume}
    Here are the previous cover letters written by the applicant: {truncated_previous_cover_letters}

    Write a new cover letter based on an adaptation of the content of the two sample cover letters, tailored to the following job posting at {company_name}: 
    {job_posting_content}"""
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=cover_letter_template,
        max_tokens=500,
        temperature=0.7,
        stop_sequences=[],
    )
    cover_letter = response.generations[0].text.strip()
    return cover_letter, cover_letter_template

def main():
    
    # Specify the path to the client_secrets.json file
    load_dotenv()
    client_secrets_path = os.environ.get("CLIENT_SECRETS_PATH")
    json_cred_path = os.path.join(os.getcwd(), client_secrets_path)

    # Set up Cohere API key and Google Drive authentication
    co = set_cohere_api_key()
    # GOOGLE DRIVE AUTH
    gauth = GoogleAuth(json_cred_path)
    gauth.LoadClientConfigFile(json_cred_path)

    # Creates local webserver and auto handles authentication.
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # Open sample cover letters and resume
    cover_letter_01, cover_letter_02 = open_and_return_cover_letters()
    with open("./resume.txt", "r") as file:
        resume = file.read()

    # Set up memory for previous cover letters
    memory = ConversationBufferMemory()

    # Read job link URLs from file
    job_links_txt_path = "./job_links_urls.txt"
    job_links = get_job_links_from_file(job_links_txt_path)

    for link in job_links:
        # Fetch job posting content
        job_posting_content = fetch_job_posting_content(link)
        if not job_posting_content:
            continue

        # Get company name, duties, and requirements from posting
        company_name = get_company_name(job_posting_content, co)
        duties = get_job_duties(job_posting_content, co)
        requirements = get_job_requirements(job_posting_content, co)

        # Get previous cover letters from memory
        previous_cover_letters = memory.load_memory_variables({})["history"]

        # Write cover letter
        cover_letter, cover_letter_template = write_cover_letter(
            cover_letter_01,
            cover_letter_02,
            company_name,
            job_posting_content,
            resume,
            previous_cover_letters,
            co
        )

        # Save cover letter to memory
        memory.save_context({"content": cover_letter_template}, {"content": cover_letter})

        # Upload cover letter to Google Drive
        cover_ltr_file = drive.CreateFile({'title': f'{company_name} Cover Letter'})
        cover_ltr_file.SetContentString(
            f"{cover_letter}\n\nHere are the job duties:\n{duties}\n\nHere are the job requirements:\n{requirements}"
        )
        cover_ltr_file.Upload()

    print("Job postings processed.")

if __name__ == "__main__":
    main()