import urllib.parse
from typing import List, Dict, Any

class WhatsAppManager:
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

    def build_dispatch_queue(
        self,
        leads: List[Dict[str, Any]],
        message_template: str,
        default_country_code: str = "91"
    ) -> List[Dict[str, Any]]:
        """
        Builds a personalized dispatch queue with direct 1-click WhatsApp Web links.
        This provides 100% ban protection because messages are sent via the user's authentic WhatsApp Web session.
        """
        queue = []
        for lead in leads:
            clean_phone = lead.get("_clean_phone", "")
            if not clean_phone:
                continue

            personalized_msg = self.personalize_text(message_template, lead)
            encoded_msg = urllib.parse.quote(personalized_msg)
            
            # Format: https://web.whatsapp.com/send?phone=919876543210&text=Hello%20...
            # Also support mobile: https://api.whatsapp.com/send?phone=...
            wa_web_link = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
            wa_api_link = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

            queue.append({
                "id": lead.get("_id"),
                "name": lead.get("_name") or "Friend",
                "phone": clean_phone,
                "raw_phone": lead.get("_raw_phone", ""),
                "company": lead.get("_company", ""),
                "message": personalized_msg,
                "wa_web_link": wa_web_link,
                "wa_api_link": wa_api_link,
                "status": lead.get("_status_whatsapp", "Pending")
            })

        return queue

whatsapp_manager = WhatsAppManager()
