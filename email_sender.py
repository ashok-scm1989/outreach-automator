import os
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, Tuple

class EmailCampaignManager:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.total = 0
        self.current = 0
        self.sent_count = 0
        self.failed_count = 0
        self.logs = []
        self.results = []

    def reset(self, total: int):
        self.is_running = True
        self.is_paused = False
        self.total = total
        self.current = 0
        self.sent_count = 0
        self.failed_count = 0
        self.logs = []
        self.results = []

    def stop(self):
        self.is_running = False

    def log(self, message: str, status: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append({"time": timestamp, "message": message, "status": status})

    @staticmethod
    def personalize_text(template: str, lead_data: Dict[str, Any]) -> str:
        """Replace {Name}, {Company}, and any {column} with lead values."""
        text = template
        for k, v in lead_data.items():
            if not k.startswith("_"):
                placeholder = f"{{{k}}}"
                text = text.replace(placeholder, str(v))
        # Handle fallback tags
        text = text.replace("{Name}", lead_data.get("_name") or lead_data.get("Name", "there"))
        text = text.replace("{Company}", lead_data.get("_company") or lead_data.get("Company", "your team"))
        return text

    def send_single_email(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        to_email: str,
        subject: str,
        body: str,
        sender_name: str = "",
        is_html: bool = False
    ) -> Tuple[bool, str]:
        """Sends a single email via SMTP with TLS/SSL handling."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
            msg["To"] = to_email

            part = MIMEText(body, "html" if is_html else "plain", "utf-8")
            msg.attach(part)

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            return True, "Delivered"
        except Exception as e:
            return False, str(e)

    def run_campaign(
        self,
        leads: List[Dict[str, Any]],
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        sender_name: str,
        subject_template: str,
        body_template: str,
        is_html: bool = False,
        min_delay: int = 5,
        max_delay: int = 10
    ):
        """Executes the bulk campaign in the background with anti-spam random delay."""
        valid_leads = [lead for lead in leads if lead.get("_email") and "@" in lead.get("_email")]
        self.reset(len(valid_leads))
        
        self.log(f"🚀 Campaign started for {len(valid_leads)} valid recipient(s).", "info")

        for lead in valid_leads:
            if not self.is_running:
                self.log("⚠️ Campaign was stopped by user.", "warning")
                break

            self.current += 1
            to_email = lead["_email"]
            name = lead.get("_name") or to_email.split("@")[0]

            # Personalize subject & body
            personalized_subject = self.personalize_text(subject_template, lead)
            personalized_body = self.personalize_text(body_template, lead)

            success, err_msg = self.send_single_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                sender_email=sender_email,
                sender_password=sender_password,
                to_email=to_email,
                subject=personalized_subject,
                body=personalized_body,
                sender_name=sender_name,
                is_html=is_html
            )

            if success:
                self.sent_count += 1
                lead["_status_email"] = "Sent"
                self.log(f"[{self.current}/{self.total}] ✅ Sent to {name} ({to_email})", "success")
            else:
                self.failed_count += 1
                lead["_status_email"] = f"Failed: {err_msg[:40]}"
                self.log(f"[{self.current}/{self.total}] ❌ Failed for {to_email}: {err_msg[:60]}", "error")

            # Anti-Spam random human-like delay
            if self.current < self.total and self.is_running:
                delay = random.uniform(min_delay, max_delay)
                self.log(f"⏳ Waiting {delay:.1f}s (anti-spam safety)...", "info")
                time.sleep(delay)

        self.is_running = False
        self.log(f"🏁 Campaign finished! Sent: {self.sent_count} | Failed: {self.failed_count}", "info")

# Global singleton manager
email_manager = EmailCampaignManager()
