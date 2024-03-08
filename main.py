from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
model = genai.GenerativeModel('gemini-pro')
from llama_parse import LlamaParse
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
import asyncio

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


def chunking(text,max_token=15000):
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
  parser = LlamaParse(
    api_key="llx-u4QviUAaditxpnyA6GmtOFLvXpvRVBCFxVYz8yyFfweodKNw",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    result_type="text"  # "markdown" and "text" are available
)
  async def read_parse(pdf):
    return await parser.aload_data(pdf_file)
  
  documents= asyncio.run(read_parse(pdf_url))
  word_count = len(documents[0].text.split(" "))
  words=documents[0].text.split(" ")
  paragraphs = word_count//3000
  start_pointer =0
  for i in range (1,paragraphs+1):
    end_pointer = start_pointer+3000
    temp = " ".join(words[start_pointer:end_pointer])
    text.append(temp)
    start_pointer = start_pointer+3000
  if(paragraphs*3000!=word_count):
    last = " ".join(words[start_pointer:word_count])
    text.append(last)
  # for section in doc.sections():
  #   text.append(section.to_text(include_children=True,recurse=True))
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

def chunking_for_embedding(pdf_url):
  delete_folder(pdf_url.split('.')[0])
  create_folder(pdf_url.split('.')[0])


  summary =  pdf_scrapper_summary(f"uploads/{pdf_url}")
  summaryText=""
  for item in summary:
    summaryText= summaryText+" "+item
  print(f'Length of the summary = {len(summary[0].split())}')
  summary_Text_List= summaryText.split()
  print(f'summary_Text_List length = {len(summary_Text_List)}')
  chunks=[]
  text=""
  if(len(summary_Text_List)<500):
     for i in range(0,len(summary_Text_List)):
      text = text+" "+summary_Text_List[i]
     chunks.append(text)
     return chunks
     
  for i in range(0,500):
     text = text+" "+summary_Text_List[i]
  chunks.append(text)
  start =500
  while(start<len(summary_Text_List)):
    text=""
    start= start-50
    if(start+500>=len(summary_Text_List)):
      for i in range(start,len(summary_Text_List)):
         text= text+" "+summary_Text_List[i]
      chunks.append(text)
      break
    for i in range(start,start+500):
      text = text +" "+summary_Text_List[i]
    chunks.append(text)
    start= start +500
    text =""
    if start>=len(summary_Text_List):
       for i in range(start-500,len(summary_Text_List)):
          text = text+" "+summary_Text_List[i]
       chunks.append(text)
       break
  print(len(chunks))
  return chunks

def extract_embedding1(chunks):
  #  model1=genai.embed_content()
  embeddings =[]
  for item in chunks:
      result = genai.embed_content(
      model="models/embedding-001",
      content=item,
      task_type="retrieval_document")
      embeddings.append(result['embedding'])
  return embeddings

 
def save_extract_embedding(pdf_url):
  find_url= check_existing_embedding('embeddings',f"{pdf_url.split('.')[0]}")
  print(f"{pdf_url.split('.')[0]}.pickle")
  if(len(find_url)==0): 
    chunks = chunking_for_embedding(pdf_url)
    create_folder('chunks')
    with open("chunks/chunks.pkl","wb") as file:
       pickle.dump(chunks,file)
    result = cloudinary.uploader.upload("chunks/chunks.pkl", resource_type="auto" ,format="pickle" , public_id = f"chunks/{pdf_url.split('.')[0]}")
    print(result['url'])
    delete_folder('chunks')
  embeddings=[]
  print(find_url)
  if(len(find_url)):
    print("embeddings  found in the cludinary database ")
    delete_folder('embeddings')
    create_folder('embeddings')
    size = len(find_url)
    for item in find_url:
      response = requests.get(item['secure_url'],stream=True)
    
      with open (item['public_id'],'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
          if chunk:
             file.write(chunk)
      with open (item['public_id'],"rb") as file:
        embedding=pickle.load(file)
      for it in embedding:
         embeddings.append(it)
    print(f"Length of total embedding {len(embeddings)}")
    
  else:
     print("Calling for creating the embedding")
     embeddings = extract_embedding1(chunks)
     delete_folder('embeddings')
     create_folder('embeddings')
     with open ('embeddings/embeddings.pkl','wb') as file:
        pickle.dump(embeddings,file)
     result = cloudinary.uploader.upload("embeddings/embeddings.pkl", resource_type="auto" ,format="pickle" , public_id = f"embeddings/{pdf_url.split('.')[0]}")
     print(result['url'])
     delete_folder('embeddings')
  return embeddings

def check_existing_embedding(folder_name,file_name):
  print(f"{folder_name} {file_name}")
  search_result = cloudinary.Search()\
    .expression(f'{folder_name}/{file_name}*')\
    .sort_by("filename", "asc")\
    .execute()
  print(len(search_result['resources']))
  return search_result['resources']



def chunk_and_embedding(pdf_url):
  embeddings = save_extract_embedding(pdf_url)
  chunks =[]
  find_url=check_existing_embedding('chunks',f"{pdf_url.split('.')[0]}")
  print(find_url)
  create_folder('chunks')
  for item in find_url:
    response = requests.get(item['secure_url'],stream=True)
  
    with open (item['public_id'],'wb') as file:
      for chunk in response.iter_content(chunk_size=1024):
        if chunk:
          file.write(chunk)
    with open (item["public_id"],"rb") as file:
       chunk=pickle.load(file)
    for it in chunk:
       chunks.append(it)
  print(f"Length of the chunks = {len(chunks)} and Length of the embedding = {len(embeddings)}")
  return {"chunks":chunks , "embeddings":embeddings}

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
@app.post("/embedding_chunk")
async def get_embedding_chunk(file:UploadFile= File(...)):
    upload_dir = "uploads"

    # Create the directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)

    # Define the file path where you want to save the uploaded file
    file_path = os.path.join(upload_dir, file.filename)

    # Open the file and write the contents
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = chunk_and_embedding(file.filename)
    delete_folder("uploads")
    return result

