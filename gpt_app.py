import openai
import os
from dotenv import load_dotenv
import requests

# SET UP GPT API
# Load environment variables from .env file
print("Loading dotenv...")
load_dotenv()
# Set up OpenAI API key
print("Loading OpenAI API key...")
openai.api_key = os.environ["OPENAI_API_KEY"]

# HELPER FUNCTIONS
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

job_links = [
    "https://www.tennibot.com/job/?id=665290?&title=Computer%20Vision%20Software%20Intern",
    "https://www.amazon.jobs/en-gb/jobs/2408098/software-development-engineer-internship-2024-us",
    "https://www.redventures.com/careers/overview?gh_jid=5916601&utm_source=Simplify&ref=Simplify",
    "https://intel.wd1.myworkdayjobs.com/en-us/external/job/Virtual-US/Undergraduate-Internship---Computer-Science--Bachelors-_JR0262659?utm_source=Simplify&ref=Simplify"
]

cover_letter_01 = ""
cover_letter_02 = ""
with open("./sample_cover_letter_01.txt", "r") as file:
    cover_letter_01 = file.read()
with open("./sample_cover_letter_02.txt", "r") as file:
    cover_letter_02 = file.read()
print("Opened both cover letters\n" + cover_letter_01 + "\n" + cover_letter_02)

for link in job_links:
    # Fetch job posting content
    job_posting_content = fetch_job_posting_content(link)
    if job_posting_content is None:
        continue

    # Find company name
    company_name_prompt = f"""
    What is the name of the company that made the following job posting?
    Just give the name of the company in your response, no extra words.
    Like for example:
    "Ford"
    "Google"
    "IMC"
    Here is the job posting:
    {job_posting_content}"""
    company_name = make_gpt_api_call(company_name_prompt)
    print("API Call complete, the company is " + company_name)

    # Generate job application draft
    application_draft = make_gpt_api_call(
        f"""
        Here are two sample cover letters: \n
        {cover_letter_01} \n 
        {cover_letter_02} \n 
        Write a new cover letter based on an adaptation of the content of the two sample cover letters to the following job posting: \n 
        {job_posting_content}
        """
    )
    print(f"The application draft for {company_name} is: \n {application_draft}")

    # Store the application draft
    print("Storing application draft to file...")
    with open(f"{company_name}_Cover_Letter.txt", "w") as file:
        file.write(application_draft)
        print("File written. Script complete.")
