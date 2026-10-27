# 🚀 Outreach Automator - Bulk Email, WhatsApp & Lead Extractor

An all-in-one, lightweight client acquisition and cold outreach automation platform built with Python (FastAPI) and modern Tailwind CSS.

Designed for freelancers, agencies, real estate consultants, gym owners, and local businesses to run personalized cold campaigns from a single spreadsheet with zero extra messaging costs and 100% anti-ban protection.

---

## 🌟 Key Features

### 1. 📁 Smart Excel / CSV Lead Processing
- Auto-detects columns: `Name`, `Email`, `Phone / Mobile`, `Company`.
- Cleans and normalizes international phone numbers with country code formatting (+91, +1, +44, +971, +61).
- Dynamic tag placeholders: `{Name}`, `{Company}`, `{Email}`, `{Phone}` automatically mapped for every row.

### 2. 📧 Personalized Bulk Email Engine
- Multi-threaded SMTP engine supporting Gmail (with Google App Password) and custom work mail domains.
- **Natural Anti-Spam Jitter Delays:** Random 5 to 8 second delay between sends to protect sender domain reputation.
- **Live Terminal & Progress Bar:** Real-time updates (*15/50 Sent Successfully*).
- **Test Email Sandbox:** Send 1-click test mail to your own inbox before launching campaigns.
- Built-in high-converting industry pitch library (Real Estate, Gym Management, E-Commerce COD, Custom Software).

### 3. 💬 1-Click WhatsApp Dispatcher (Zero Ban Risk)
- Eliminates manual typing and copy-pasting numbers one by one.
- Generates 1-click personalized WhatsApp Web links (`https://web.whatsapp.com/send?phone=...&text=...`).
- Click **"Send WA"** -> Opens verified WhatsApp Web with contact & personalized pitch pre-filled -> Press **Enter** to send.
- **Zero Ban Risk:** Operates strictly through your genuine browser session without brittle unofficial API bots.

### 4. 🔍 Real Estate & Local Business Lead Finder
- **City-Specific Extractor:** Generates targeted real estate agent and broker leads for top markets (Austin TX, Miami FL, Delhi NCR, Mumbai, Dubai) with verified emails and direct phone numbers.
- **Agency Website Email Hunter:** Crawls brokerage homepages, `/contact`, `/about`, and `/team` pages to regex-extract direct agent emails (`@compass.com`, `@kw.com`, `@luxuryrealty.com`).
- **Direct Excel Export:** Saves all discovered leads straight to `.xlsx`.

### 5. 📥 Campaign Results Export
- Export updated Excel files tracking delivery status for each lead (`Email_Status: Sent`, `WhatsApp_Status: Sent`).

---

## 🏗️ Architecture

```
outreach-automator/
├── server.py              # FastAPI backend & REST API endpoints
├── excel_parser.py        # Spreadsheet parser & phone normalizer
├── email_sender.py        # Multi-threaded SMTP campaign runner with jitter delays
├── whatsapp_dispatcher.py # 1-click WhatsApp link generator
├── lead_finder.py         # Real estate lead extractor & website email crawler
├── templates/
│   └── index.html         # Responsive Tailwind CSS dashboard
├── Ashok_Test_Leads.xlsx  # Ready-to-test sample leads file
├── Sample_Leads.xlsx      # Standard sample leads file
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Pip

### 1. Installation
```bash
git clone https://github.com/ashok-scm1989/outreach-automator.git
cd outreach-automator
pip install -r requirements.txt
```

### 2. Run Application
```bash
python server.py
```
Open your browser and navigate to:
👉 **`http://localhost:8500`**

---

## 🛡️ Anti-Spam & Deliverability Guidelines

| Channel | Recommended Daily Limit | Best Practice |
| :--- | :--- | :--- |
| **Gmail (Free)** | 40 - 60 emails / day | Keep 5-8 second random delays enabled |
| **Google Workspace (Paid)** | 150 - 300 emails / day | Use custom sender name and clear subject lines |
| **WhatsApp Web** | 25 - 40 chats / day | Dispatch with 1-click flow; personalize recipient name |

---

## 📄 License
MIT License. Built for high-efficiency client outreach.
