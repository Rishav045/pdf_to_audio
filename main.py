from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
model = genai.GenerativeModel('gemini-pro')
import pathlib
import os
import json
import pickle 
import requests
from llmsherpa.readers import LayoutPDFReader
import gtts
import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.utils
import shutil

genai.configure(api_key="AIzaSyBjJkjihTUrVF0JbVEBLUZ5kwZyzzJzROs")
cloudinary.config(cloud_name="dhxj4w8th",api_key="159331216765633",api_secret="cbYQHEPDovgv9NgYHvWy4Krr-sk")
llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
pdf_reader = LayoutPDFReader(llmsherpa_api_url)

def create_folder(folder_path):
    try:
        # Check if the folder doesn't exist
        if not os.path.exists(folder_path):
            # Create the folder
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created successfully.")
        else:
            print(f"Folder '{folder_path}' already exists.")

    except Exception as e:
        print(f"Error creating folder '{folder_path}': {str(e)}")

def delete_folder(folder_path):
    try:
        # Remove the folder and its contents recursively
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' and its contents deleted successfully.")

    except Exception as e:
        print(f"Error deleting folder '{folder_path}': {str(e)}")


def chunking(text,max_token=10000):
  required=[]
  chunk =""
  counter= 0
  for item in text:
    # print(len(item))
    counter=counter+len(item)
    chunk = chunk + item
    if(counter>=max_token):
      if(len(chunk)>30000):
        first_half = chunk[:int(len(chunk)/2)]
        second_half=chunk[int(len(chunk)/2):]
        required.append(first_half)
        required.append(second_half)
        chunk=""
        counter=0
        continue
      required.append(chunk)
      counter =0
      chunk=""
  return required

def pdf_scrapper_summary(pdf_url):
  doc = pdf_reader.read_pdf(pdf_url)
  sections = []
  for section in doc.sections():
    sections.append(section.title)
  text=[]
  summary=[]
  print("Extracting the section text.....")
  for section in doc.sections():
    text.append(section.to_text(include_children=True,recurse=True))
  print("Text extracted successfully !!!")
  
  print("Chunking the text ....")
  result = chunking(text)
  print("Chunking Completed!!")
  count=0
  for item in result:
    print(f"Summarizing and paraphrasing the paragaraph no {count+1}")
    response = model.generate_content("Consider you are a teacher so explain briefly following text simply in form of paragraph in "+str((0.75)*len(item))+" words  :-  "+item)
    print(response.text.replace('*',''))

    print("--------------------------------------------------------------------------")
    print(f'length of the text = {len(item.split())}  and now length of the response from  geninmi = {len(response.text.split())}')
    summary.append(response.text.replace('*',''))
    count = count +1
  return summary

def summary1(pdf_url):
  delete_folder(pdf_url.split('.')[0])
  create_folder(pdf_url.split('.')[0])
  
  summary = pdf_scrapper_summary(f"uploads/{pdf_url}")
  return summary

def summary_to_audio(pdf_url):
  delete_folder(pdf_url.split('.')[0])
  create_folder(pdf_url.split('.')[0])
  
  summary = pdf_scrapper_summary(f"uploads/{pdf_url}")
  print(summary)
  links=[]
  count =0
  for item in summary:
     sound = gtts.gTTS(item,lang="hi",slow=False)
     print(f'converting to audio {count+1} paragraph')
     sound.save(pdf_url.split('.')[0]+'/'+f'{count+1}.mp3')
     upload_result = cloudinary.uploader.upload(pdf_url.split('.')[0]+'/'+f'{count+1}.mp3',resource_type="video",format="mp3",public_id=pdf_url.split('.')[0]+'/'+f'{count+1}')
     links.append(upload_result['url'])
     print(upload_result['url'])
     count= count+1
  delete_folder(pdf_url.split('.')[0])
  return links

app = FastAPI()

app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"]
)

@app.get("/")
def root():
   return {"Message":"Hello World"}

@app.post("/summary")
async def getSummary(file : UploadFile =File(...)):
#    contents = file.read()
#    print(f"filename {file.filename} filetype {file.content_type}")
   upload_dir = "uploads"

    # Create the directory if it doesn't exist
   os.makedirs(upload_dir, exist_ok=True)

    # Define the file path where you want to save the uploaded file
   file_path = os.path.join(upload_dir, file.filename)

    # Open the file and write the contents
   with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
  
   
   summary=summary1(file.filename)
   print(summary)
   delete_folder("uploads")
   return {"summary":summary}

@app.post("/audio")
async def getAudio(file : UploadFile= File(...)):

  # contents =await file.read()
  # print(contents)
  upload_dir = "uploads"

    # Create the directory if it doesn't exist
  os.makedirs(upload_dir, exist_ok=True)

    # Define the file path where you want to save the uploaded file
  file_path = os.path.join(upload_dir, file.filename)

    # Open the file and write the contents
  with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
  lists= summary_to_audio(file.filename)
  delete_folder("uploads")
  return {"lists":lists}
  
     
  # return {"filename":file.filename }


