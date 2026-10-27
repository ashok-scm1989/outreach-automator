import os
import shutil
import threading
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
import uvicorn

from excel_parser import parse_leads_file
from email_sender import email_manager
from whatsapp_dispatcher import whatsapp_manager
from lead_finder import generate_real_estate_leads, save_leads_to_excel, crawl_domain_for_emails

app = FastAPI(title="Outreach Automator - Bulk Email & WhatsApp")

# In-memory storage for current session
SESSION_DATA = {
    "leads": [],
    "columns": [],
    "filename": ""
}

class EmailCampaignRequest(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str
    sender_password: str
    sender_name: str = ""
    subject: str
    body: str
    is_html: bool = False
    min_delay: int = 5
    max_delay: int = 8

class TestEmailRequest(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str
    sender_password: str
    sender_name: str = ""
    test_to: str
    subject: str
    body: str

class WhatsAppRequest(BaseModel):
    message_template: str
    default_country_code: str = "91"

class StatusUpdateRequest(BaseModel):
    lead_id: int
    channel: str  # "email" or "whatsapp"
    status: str   # "Sent", "Failed", etc.

class GenerateLeadsRequest(BaseModel):
    city: str = "Austin"
    custom_domains: Optional[List[str]] = None
    default_country_code: str = "1"

class ScrapeWebsiteRequest(BaseModel):
    website: str
    default_country_code: str = "1"

class GoogleMapsImportRequest(BaseModel):
    items: List[Dict[str, Any]]
    default_country_code: str = "1"

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/upload")
async def upload_leads_file(
    file: UploadFile = File(...),
    default_country_code: str = Form("91")
):
    """Uploads and parses an Excel or CSV file."""
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        leads, columns = parse_leads_file(file_path, default_country_code=default_country_code)
        SESSION_DATA["leads"] = leads
        SESSION_DATA["columns"] = columns
        SESSION_DATA["filename"] = file.filename
        
        email_count = sum(1 for l in leads if l.get("_email") and "@" in l.get("_email"))
        phone_count = sum(1 for l in leads if l.get("_clean_phone"))
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "total_leads": len(leads),
            "email_count": email_count,
            "phone_count": phone_count,
            "columns": columns,
            "preview": leads[:50]  # First 50 rows for table preview
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/load-sample")
async def load_sample_file(default_country_code: str = "91"):
    """Loads pre-generated Ashok Test Leads directly."""
    sample_path = os.path.join(os.path.dirname(__file__), "Ashok_Test_Leads.xlsx")
    if not os.path.exists(sample_path):
        sample_path = os.path.join(os.path.dirname(__file__), "Sample_Leads.xlsx")
    
    try:
        leads, columns = parse_leads_file(sample_path, default_country_code=default_country_code)
        SESSION_DATA["leads"] = leads
        SESSION_DATA["columns"] = columns
        SESSION_DATA["filename"] = os.path.basename(sample_path)
        
        email_count = sum(1 for l in leads if l.get("_email") and "@" in l.get("_email"))
        phone_count = sum(1 for l in leads if l.get("_clean_phone"))
        
        return JSONResponse(content={
            "success": True,
            "filename": os.path.basename(sample_path),
            "total_leads": len(leads),
            "email_count": email_count,
            "phone_count": phone_count,
            "columns": columns,
            "preview": leads[:50]
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/download-sample")
async def download_sample():
    """Download Ashok_Test_Leads.xlsx directly to user machine."""
    path = os.path.join(os.path.dirname(__file__), "Ashok_Test_Leads.xlsx")
    return FileResponse(path, filename="Ashok_Test_Leads.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/generate-leads")
async def generate_leads_endpoint(req: GenerateLeadsRequest):
    """Generates real estate leads for the selected city and writes them to an Excel file."""
    try:
        raw_leads = generate_real_estate_leads(city=req.city, extra_domains=req.custom_domains)
        filename = f"Real_Estate_Leads_{req.city.replace(' ', '_')}.xlsx"
        file_path = save_leads_to_excel(raw_leads, filename=filename)
        
        leads, columns = parse_leads_file(file_path, default_country_code=req.default_country_code)
        SESSION_DATA["leads"] = leads
        SESSION_DATA["columns"] = columns
        SESSION_DATA["filename"] = filename
        
        email_count = sum(1 for l in leads if l.get("_email") and "@" in l.get("_email"))
        phone_count = sum(1 for l in leads if l.get("_clean_phone"))
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "total_leads": len(leads),
            "email_count": email_count,
            "phone_count": phone_count,
            "columns": columns,
            "preview": leads[:50]
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/scrape-website")
async def scrape_website_endpoint(req: ScrapeWebsiteRequest):
    """Scrapes emails and phones from a single company or broker website."""
    try:
        emails, phones = crawl_domain_for_emails(req.website)
        if not emails and not phones:
            return JSONResponse(status_code=400, content={"success": False, "error": f"No public emails found on {req.website}"})
        
        company = req.website.replace("https://", "").replace("http://", "").split("/")[0].title()
        new_leads = []
        for em in emails:
            name = em.split("@")[0].replace(".", " ").title()
            new_leads.append({
                "name": name,
                "email": em,
                "phone": phones[0] if phones else "",
                "company": company,
                "website": req.website
            })
            
        filename = f"Scraped_{company}_Leads.xlsx"
        file_path = save_leads_to_excel(new_leads, filename=filename)
        leads, columns = parse_leads_file(file_path, default_country_code=req.default_country_code)
        
        if SESSION_DATA.get("leads"):
            start_id = len(SESSION_DATA["leads"]) + 1
            for idx, nl in enumerate(leads):
                nl["_id"] = start_id + idx
                SESSION_DATA["leads"].append(nl)
        else:
            SESSION_DATA["leads"] = leads
            SESSION_DATA["columns"] = columns
            SESSION_DATA["filename"] = filename

        return JSONResponse(content={
            "success": True,
            "found_emails": len(emails),
            "found_phones": len(phones),
            "preview": new_leads,
            "total_leads": len(SESSION_DATA["leads"])
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/download-leads-excel")
async def download_generated_leads():
    """Download generated leads Excel file."""
    filename = SESSION_DATA.get("filename", "Real_Estate_Leads.xlsx")
    path = os.path.join(os.path.dirname(__file__), "uploads", filename)
    if not os.path.exists(path):
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
        for f in os.listdir(upload_dir):
            if f.endswith(".xlsx"):
                path = os.path.join(upload_dir, f)
                filename = f
                break
    return FileResponse(path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/test-email")
async def send_test_email(req: TestEmailRequest):
    """Sends a single test email to verify credentials and layout."""
    success, msg = email_manager.send_single_email(
        smtp_host=req.smtp_host,
        smtp_port=req.smtp_port,
        sender_email=req.sender_email,
        sender_password=req.sender_password,
        to_email=req.test_to,
        subject=f"[TEST] {req.subject}",
        body=req.body,
        sender_name=req.sender_name
    )
    if success:
        return JSONResponse(content={"success": True, "message": "Test email sent successfully! Check your inbox."})
    else:
        return JSONResponse(status_code=400, content={"success": False, "error": msg})

@app.post("/api/send-emails")
async def start_email_campaign(req: EmailCampaignRequest):
    """Triggers bulk email sending in background."""
    if not SESSION_DATA["leads"]:
        return JSONResponse(status_code=400, content={"error": "No leads loaded. Please upload an Excel file first."})
        
    if email_manager.is_running:
        return JSONResponse(status_code=400, content={"error": "A campaign is already running."})

    # Start campaign in a daemon background thread
    t = threading.Thread(
        target=email_manager.run_campaign,
        kwargs={
            "leads": SESSION_DATA["leads"],
            "smtp_host": req.smtp_host,
            "smtp_port": req.smtp_port,
            "sender_email": req.sender_email,
            "sender_password": req.sender_password,
            "sender_name": req.sender_name,
            "subject_template": req.subject,
            "body_template": req.body,
            "is_html": req.is_html,
            "min_delay": req.min_delay,
            "max_delay": req.max_delay
        },
        daemon=True
    )
    t.start()
    return JSONResponse(content={"success": True, "message": "Email campaign launched!"})

@app.post("/api/stop-emails")
async def stop_email_campaign():
    """Stops the active email campaign."""
    email_manager.stop()
    return JSONResponse(content={"success": True, "message": "Stopping campaign..."})

@app.get("/api/email-status")
async def get_email_status():
    """Returns live progress metrics and logs for UI progress bar."""
    return JSONResponse(content={
        "is_running": email_manager.is_running,
        "total": email_manager.total,
        "current": email_manager.current,
        "sent_count": email_manager.sent_count,
        "failed_count": email_manager.failed_count,
        "progress_pct": round((email_manager.current / email_manager.total * 100), 1) if email_manager.total > 0 else 0,
        "logs": email_manager.logs[-20:]  # Recent 20 logs
    })

@app.post("/api/generate-whatsapp")
async def generate_whatsapp_queue(req: WhatsAppRequest):
    """Builds personalized 1-click WhatsApp queue from current leads."""
    if not SESSION_DATA["leads"]:
        return JSONResponse(status_code=400, content={"error": "No leads loaded. Please upload an Excel file first."})

    queue = whatsapp_manager.build_dispatch_queue(
        leads=SESSION_DATA["leads"],
        message_template=req.message_template,
        default_country_code=req.default_country_code
    )
    return JSONResponse(content={"success": True, "total": len(queue), "queue": queue})

@app.post("/api/update-lead-status")
async def update_lead_status(req: StatusUpdateRequest):
    """Updates status of lead in memory when dispatched."""
    for l in SESSION_DATA["leads"]:
        if l.get("_id") == req.lead_id:
            if req.channel == "whatsapp":
                l["_status_whatsapp"] = req.status
            elif req.channel == "email":
                l["_status_email"] = req.status
            return JSONResponse(content={"success": True})
    return JSONResponse(status_code=404, content={"error": "Lead ID not found"})

@app.get("/api/export-results")
async def export_results():
    """Exports updated leads list with status to Excel."""
    if not SESSION_DATA["leads"]:
        raise HTTPException(status_code=400, detail="No leads available to export.")

    df = pd.DataFrame(SESSION_DATA["leads"])
    # Clean internal helper columns for export
    export_df = df[[col for col in df.columns if not col.startswith("_")]].copy()
    export_df["Email_Status"] = df["_status_email"]
    export_df["WhatsApp_Status"] = df["_status_whatsapp"]

    export_path = os.path.join(os.path.dirname(__file__), "uploads", "Outreach_Results.xlsx")
    export_df.to_excel(export_path, index=False)
    return FileResponse(export_path, filename="Outreach_Results.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    print("\nStarting Outreach Automator Dashboard at: http://localhost:8500")
    uvicorn.run("server:app", host="127.0.0.1", port=8500, reload=False)
