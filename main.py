import base64
from datetime import datetime
import json
import time
from uuid import UUID
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import qrcode
from sqlmodel import Session, select

from middlewares.logging import log_incoming_requests
from models.invoice_model import Invoice
from models.invoice_stuff_link_model import InvoiceStuffLink
from models.stuff_model import Stuff
from session import get_db

load_dotenv()
INVOICE_PDF = os.getenv("INVOICE_PDF")
INVOICE_PICS = os.getenv("INVOICE_PICS")
STUFF_PICS = os.getenv("STUFF_PICS")
QR_CODE_PICS = os.getenv("QR_CODE_PICS")

os.makedirs(INVOICE_PDF, exist_ok=True)
os.makedirs(INVOICE_PICS, exist_ok=True)
os.makedirs(STUFF_PICS, exist_ok=True)
os.makedirs(QR_CODE_PICS, exist_ok=True)


app = FastAPI()
app.middleware("http")(log_incoming_requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "server is runnnig"}

@app.post("/upload/invoice")
async def upload_invoices(invoice_file: UploadFile, stuff_file: UploadFile, session: Session = Depends(get_db)):
    """Upload Invoice can be of type PDF or .jpeg or .png or jpg only"""
    start = time.time()
    print(start)  
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if invoice_file.filename.endswith(".pdf"):
        original_ext = os.path.splitext(invoice_file.filename)[1]
        new_invoice_file_name = f"{os.path.splitext(invoice_file.filename)[0]}__{timestamp}{original_ext}"
        invoice_file_location = os.path.join(INVOICE_PDF, new_invoice_file_name)

    elif invoice_file.filename.endswith((".jpg",".png",".jpeg")):
        original_ext = os.path.splitext(invoice_file.filename)[1]
        new_invoice_file_name = f"{os.path.splitext(invoice_file.filename)[0]}__{timestamp}{original_ext}"
        invoice_file_location = os.path.join(INVOICE_PICS, new_invoice_file_name)
    
    else:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if stuff_file.filename.endswith((".jpg",".png",".jpeg")):
        original_ext = os.path.splitext(stuff_file.filename)[1]
        new_stuff_file_name = f"{os.path.splitext(stuff_file.filename)[0]}__{timestamp}{original_ext}"
        stuff_file_location = os.path.join(STUFF_PICS, new_stuff_file_name)
    
    else:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        with open(invoice_file_location, "wb") as f:
            content = await invoice_file.read()
            f.write(content)
        new_invoice = Invoice(file_path=invoice_file_location,file_name=new_invoice_file_name)
        session.add(new_invoice)    
        
        with open(stuff_file_location, "wb") as f:
            content = await stuff_file.read()
            f.write(content)
        new_stuff = Stuff(file_path=stuff_file_location,file_name=new_stuff_file_name)
        session.add(new_stuff)
        session.commit()
        
        link = InvoiceStuffLink(invoice_id=new_invoice.id, stuff_id=new_stuff.id)
        session.add(link)
        session.commit()
        session.refresh(new_stuff)
        
        qr_data={"stuff_filename":new_stuff_file_name, "stuff_id":new_stuff.id}
        start3=time.time()
        qr_image_path=generate_qr(qr_data)
        end3 = time.time()
        print(f"QR_gen Execution time: {end3 - start3:.6f} seconds")
        
        # stuff_image = encode_image_to_base64(qr_image_path)
        
        end = time.time()
        print(f"Master Execution time: {end - start:.6f} seconds")
        return FileResponse(qr_image_path, media_type="image/jpeg",filename="qr.jpg" )
        
    except Exception as e:
        session.rollback()  # Roll back DB changes
        print(f"Error occurred: {e}")  # or use `logging.error(...)`
        raise HTTPException(status_code=500, detail="Failed to upload files and link data.")
        
        
        
@app.get("/stuff")
async def fetch_stuff(qr_data_id:UUID, session: Session = Depends(get_db)):
    """upload the qr data to fetch related file"""
    
    stuff = session.exec(select(Stuff).where(Stuff.id == qr_data_id)).first()
    if stuff is None:
        raise HTTPException(status_code=404, detail="Stuff id not found")
    related_invoice = stuff.invoice
    
    stuff_image = encode_image_to_base64(stuff.file_path)
    invoice_image = encode_image_to_base64(related_invoice.file_path)
    
    if related_invoice.file_name.endswith(".pdf"):
        return JSONResponse(content={
        "stuff": f"data:image/jpeg;base64,{stuff_image}",
        "invoice_pdf": f"data:application/pdf;base64,{invoice_image}",
    })
        
    return JSONResponse(content={
        "stuff": f"data:image/jpeg;base64,{stuff_image}",
        "invoice_image": f"data:image/jpeg;base64,{invoice_image}",
    })


@app.get("/stuff/all")
async def fetch_stuff(session: Session = Depends(get_db)):    
    """upload the qr data to fetch related file"""
    stuff = session.exec(select(Stuff)).all()
    return stuff


def encode_image_to_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def generate_qr(data):
    qr = qrcode.QRCode(
        version=1,  # controls the size of the QR Code (1-40)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    serializable_data = {
        k: str(v) if isinstance(v, UUID) else v
        for k, v in data.items()
    }
    qr.add_data(json.dumps(serializable_data))
    print(json.dumps(serializable_data))
    qr.make(fit=True)

    file_path = os.path.join(QR_CODE_PICS, f"QR__{data['stuff_filename']}.png")
    img = qr.make_image(fill="black", back_color="white")
    img.save(file_path)
    
    return file_path