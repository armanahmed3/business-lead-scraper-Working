import random
import os
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AIEmailGenerator:
    def __init__(self):
        self.email_templates = {
            'professional': {
                'greetings': ["Dear {name}", "Hello {name}", "Hi {name}", "Good day {name}"],
                'intros': [
                    "I hope this email finds you well.",
                    "I hope you're having a great day.",
                    "I trust this message reaches you in good health.",
                    "I hope everything is going well at {company}."
                ],
                'bodies': [
                    "I wanted to reach out regarding an exciting opportunity that I believe would be of great interest to {company}. Our innovative solution has helped numerous companies in your industry achieve significant growth and efficiency improvements.",
                    "I came across {company} and was impressed by your recent achievements. I have an opportunity that could help you take your business to the next level.",
                    "I'm reaching out because I believe our solution could provide significant value to {company}. We've helped similar companies achieve remarkable results.",
                    "I wanted to share an exclusive opportunity that I think would be perfect for {company}. Our solution has been proven to deliver measurable results."
                ],
                'value_props': [
                    "Our solution has helped companies achieve up to 40% improvement in efficiency.",
                    "We've seen an average ROI of 300% within the first year.",
                    "Our clients typically see a 50% reduction in operational costs.",
                    "We've helped companies increase revenue by an average of 25%."
                ],
                'ctas': [
                    "I would appreciate the opportunity to schedule a brief 15-minute call to discuss how this could benefit {company}.",
                    "Would you be interested in a quick conversation to explore this opportunity?",
                    "I'd love to show you how this could work for {company}. Are you available for a brief call?",
                    "Could we schedule a short meeting to discuss this further?"
                ],
                'closings': ["Best regards", "Warm regards", "Sincerely", "Thank you for your time"]
            },
            'casual': {
                'greetings': ["Hi {name}", "Hey {name}", "Hello {name}", "Hi there {name}"],
                'intros': [
                    "Hope you're doing well!",
                    "How's it going?",
                    "Hope everything's great at {company}!",
                    "Hope you're having a good day!"
                ],
                'bodies': [
                    "I came across {company} and was really impressed by what you're doing. I thought you might be interested in something that could help take your business to the next level.",
                    "I've been following {company} and I'm really excited about what you're building. I have something that might be perfect for you.",
                    "I stumbled upon {company} and was blown away by your work. I think I have something that could be really valuable for you.",
                    "I've been keeping an eye on {company} and I'm really impressed. I have an opportunity that I think you'd find interesting."
                ],
                'value_props': [
                    "It's pretty cool stuff - we've helped companies like yours save tons of time and money.",
                    "The results are pretty amazing - our clients typically see huge improvements within the first month.",
                    "It's really impressive what we've been able to help companies achieve.",
                    "The feedback has been incredible - companies are seeing massive improvements."
                ],
                'ctas': [
                    "Want to grab a virtual coffee and chat about it?",
                    "Got 10 minutes for a quick call? I'd love to show you what we can do.",
                    "Want to hop on a quick call to see how this could work for you?",
                    "Interested in a brief demo? I think you'll love what you see."
                ],
                'closings': ["Cheers", "Talk soon", "Looking forward to hearing from you", "Thanks!"]
            },
            'urgent': {
                'greetings': ["Dear {name}", "Hello {name}", "Hi {name}"],
                'intros': [
                    "I'm reaching out with an urgent opportunity that requires immediate attention.",
                    "I need to bring something important to your attention.",
                    "This is time-sensitive and I wanted to reach out immediately.",
                    "I have an urgent matter that I believe is critical for {company}."
                ],
                'bodies': [
                    "This exclusive opportunity is only available for a limited time and could significantly impact {company}'s growth. Our solution has helped companies achieve 50% faster results compared to traditional methods.",
                    "This time-sensitive opportunity could transform {company}'s operations. Don't miss out on this chance to gain a competitive advantage.",
                    "This limited-time offer could revolutionize how {company} operates. Time is of the essence and immediate action is required.",
                    "This urgent opportunity could provide {company} with a significant competitive edge. The window for action is closing quickly."
                ],
                'value_props': [
                    "This offer expires in 48 hours and won't be available again.",
                    "Limited spots available - first come, first served.",
                    "This exclusive opportunity is only available to select companies.",
                    "Time-sensitive offer with significant benefits."
                ],
                'ctas': [
                    "Please respond immediately to secure your spot.",
                    "Time is critical - please reply today to discuss next steps.",
                    "This requires immediate action - please contact me today.",
                    "Don't miss out - respond now to take advantage of this opportunity."
                ],
                'closings': ["Best regards", "Sincerely", "Urgently yours"]
            }
        }
        
        self.subject_templates = {
            'professional': [
                "{company} - Exclusive Opportunity",
                "Partnership Opportunity for {company}",
                "Growth Opportunity for {company}",
                "Innovation Partnership with {company}",
                "Strategic Opportunity for {company}"
            ],
            'casual': [
                "Quick question about {company}",
                "Something you might like",
                "Quick chat about {company}",
                "Thought you'd find this interesting",
                "Quick question for you"
            ],
            'urgent': [
                "URGENT: Limited Time Opportunity for {company}",
                "Time-Sensitive: {company} Growth Opportunity",
                "Action Required: {company} Partnership",
                "Immediate: {company} Exclusive Offer",
                "Deadline: {company} Opportunity"
            ]
        }
    
    def generate_email(self, lead_data: Dict, campaign_type: str = 'professional', 
                     api_key: str = None) -> Dict[str, str]:
        """Generate personalized email content using AI or templates"""
        
        # Try AI generation first if API key is provided
        if api_key:
            try:
                ai_content = self._generate_with_openrouter(lead_data, campaign_type, api_key)
                if ai_content:
                    # Merge with lead data for consistency
                    ai_content.update({
                        'lead_email': lead_data.get('email', ''),
                        'lead_company': lead_data.get('company', ''),
                        'campaign_type': campaign_type
                    })
                    return ai_content
            except Exception as e:
                print(f"AI Generation failed, falling back to templates: {e}")

        # Fallback to template system
        template = self.email_templates.get(campaign_type, self.email_templates['professional'])
        subject_template = self.subject_templates.get(campaign_type, self.subject_templates['professional'])
        
        # Generate subject line
        subject = random.choice(subject_template).format(
            name=lead_data.get('name', 'Valued Customer'),
            company=lead_data.get('company', 'Your Company')
        )
        
        # Generate email body
        greeting = random.choice(template['greetings']).format(name=lead_data.get('name', 'Valued Customer'))
        intro = random.choice(template['intros']).format(company=lead_data.get('company', 'your company'))
        body_text = random.choice(template['bodies']).format(
            name=lead_data.get('name', 'Valued Customer'),
            company=lead_data.get('company', 'your company'),
            title=lead_data.get('title', 'valued professional')
        )
        value_prop = random.choice(template['value_props'])
        cta = random.choice(template['ctas']).format(company=lead_data.get('company', 'your company'))
        closing = random.choice(template['closings'])
        
        sender_name = os.getenv('SENDER_NAME', 'Your Name')
        body = f"{greeting},\n\n{intro}\n\n{body_text}\n\n{value_prop}\n\n{cta}\n\n{closing},\n{sender_name}"
        
        # Personalize placeholders - explicitly handle potential KeyError if format string is complex
        try:
            body = body.format(
                name=lead_data.get('name', 'Valued Customer'),
                company=lead_data.get('company', 'your company'),
                title=lead_data.get('title', 'valued professional'),
                industry=lead_data.get('industry', 'your industry')
            )
        except KeyError:
             pass # Fallback to already partially formatted body
        
        return {
            'subject': subject,
            'body': body,
            'lead_name': lead_data.get('name', ''),
            'lead_email': lead_data.get('email', ''),
            'lead_company': lead_data.get('company', ''),
            'type': 'template',
            'generated_at': datetime.now().isoformat()
        }

    def _generate_with_openrouter(self, lead_data: Dict, tone: str, api_key: str) -> Optional[Dict]:
        """Call OpenRouter API to generate high-quality email"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "LeadAI Pro Email Generator",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Generate a highly personalized cold email for a lead with the following details:
        Name: {lead_data.get('name', 'Unknown')}
        Company: {lead_data.get('company', 'Unknown')}
        Title: {lead_data.get('title', 'Professional')}
        Industry: {lead_data.get('industry', 'Business')}
        
        Tone: {tone}
        Requirement: The email should be engaging, professional, and focus on delivering value. 
        Format the response as a JSON object with 'subject' and 'body' keys.
        """
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-3-12b:free",
                    "messages": [
                        {"role": "system", "content": "You are an expert sales copywriter. Return ONLY JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": { "type": "json_object" }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # Strip potential markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                    
                res_json = json.loads(content)
                return {
                    'subject': res_json.get('subject', 'Opportunity for you'),
                    'body': res_json.get('body', ''),
                    'lead_name': lead_data.get('name', ''),
                    'type': 'ai_generated',
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"OpenRouter Request error: {e}")
        return None

# Global AI email generator instance
ai_email_generator = AIEmailGenerator()
