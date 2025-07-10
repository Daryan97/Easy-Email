import re
import json
from datetime import datetime

from flask import jsonify, make_response, render_template
from flask_restx import abort
from flask_jwt_extended import current_user

from init import openai, workersai, db, fernet, create_logger
from functions.oauth import Google, Microsoft
from functions.email import Email
from models.chat import Chat, ChatMessages
from models.contact import Contact
from models.oauth import Oauth

logger = create_logger(__name__)

# Constants
backslash_n      = "\n"
model            = "pai-001"
temperature      = 0.6
max_history      = 5
today_date_time  = datetime.now().strftime("%A, %d %B %Y")

system_prompt = f"""You are an email generator AI. Your task is to generate an email based on the provided sender, recipient details, instruction, tone, and length. Use newline characters to separate all sections, lines, and bullet points—do not combine content into a single line unless the user explicitly requests it. Sometimes, use a double newline to clearly separate major sections or paragraphs when appropriate. Output only the email content without any explanations or meta-comments.

Output format:
Subject: [subject]

Body:
[body]

Ensure:
- The email is concise and follows the given instruction.
- No placeholders (e.g., "[your name]") are included.
- If the user requests edits, apply only the specified changes without altering the rest of the email.
- Use single newlines for line breaks and double newlines to separate major paragraphs or sections.
- Incorporate relevant company details and education background where it enhances the tone or context.
- Adapt the level of formality based on the specified tone, using educational credentials or company information as appropriate.

Today's date is {today_date_time}."""

LENGTH_MAP = {
    "short":      "Short (50-125 words)",
    "medium":     "Medium (125-250 words)",
    "long":       "Long (250-500 words)",
    "extra_long": "Extra Long (500+ words)"
}


class ChatAssistant:
    """Encapsulates all chat/email flows in Diyari.ai, refactored for clarity."""

    @staticmethod
    def _get_contact_info(raw):
        """Normalize a raw contact dict (by id or email) into a standard dict."""
        if "id" in raw:
            cid = raw["id"]
            c = Contact.query.get(cid)
            if not c or cid not in [ct.id for ct in current_user.contacts]:
                abort(400, f"Contact {cid} not found")
            return {
                "name":       c.name,
                "email":      c.email,
                "company":    c.company,
                "work_title": c.work_title,
                "college":    c.college,
                "major":      c.major,
                "phone_code": c.phone_code,
                "phone_number": c.phone_number
            }
        elif "email" in raw:
            return {
                "name":        raw.get("name"),
                "email":       raw["email"],
                "company":     raw.get("company"),
                "work_title":  raw.get("work_title"),
                "college":     raw.get("college"),
                "major":       raw.get("major"),
                "phone_code":  raw.get("phone_code"),
                "phone_number":raw.get("phone_number")
            }
        else:
            abort(400, "You must provide either contact IDs or emails")

    @staticmethod
    def format_contact(contacts, label="To"):
        """Render a list of contact dicts into the AI prompt block."""
        if not contacts:
            return None

        out = f"{label}: {backslash_n}"
        for idx, c in enumerate(contacts, start=1):
            if c.get("name"):
                out += f"Name: {c['name']}{backslash_n}"
            out += f"Email: {c['email']}{backslash_n}"
            if c.get("company"):
                wt = c.get("work_title") or ""
                out += f"Company: {c['company']} - {wt}{backslash_n}"
            if c.get("college"):
                out += f"College: {c['college']} - {c.get('major')}{backslash_n}"
            if c.get("phone_code") and c.get("phone_number"):
                out += f"Phone: {c['phone_code']}{c['phone_number']}"
            if idx < len(contacts):
                out += backslash_n
        return out

    @staticmethod
    def seperate_contacts(contacts):
        """
        Accepts a list of buckets like:
            [{"to":[...], "cc":[...], "bcc":[...]}]
        and returns three flat lists of normalized contact dicts.
        """
        to, cc, bcc = [], [], []
        for bucket in contacts:
            for raw in bucket.get("to", []):
                to.append(ChatAssistant._get_contact_info(raw))
            for raw in bucket.get("cc", []):
                cc.append(ChatAssistant._get_contact_info(raw))
            for raw in bucket.get("bcc", []):
                bcc.append(ChatAssistant._get_contact_info(raw))
        return to, cc, bcc

    @staticmethod
    def get_chat_history(chat_id):
        """Fetch last `max_history` messages, decrypt & rehydrate JSON, return AI-friendly list."""
        chat = Chat.query.get(chat_id)
        if not chat:
            abort(404, "Chat not found")

        msgs = (
            ChatMessages.query
            .filter_by(chat_id=chat_id)
            .order_by(ChatMessages.id.desc())
            .limit(max_history)
            .all()
        )

        history = []
        for m in reversed(msgs):
            try:
                data = json.loads(fernet.decrypt(m.data.encode()).decode())
            except:
                abort(400, "Error decrypting chat messages")

            if m.chat_type == "assistant":
                content = (
                    f"Subject: {data['subject']}{backslash_n}"
                    f"Body: {data['body']}{backslash_n}"
                )
                history.append({"role": "assistant", "content": content})
            else:
                to, cc, bcc = ChatAssistant.seperate_contacts(data["contacts"])
                t_str  = ChatAssistant.format_contact(to,  "To")  or ""
                cc_str = ChatAssistant.format_contact(cc,  "CC") or ""
                bcc_str= ChatAssistant.format_contact(bcc, "BCC") or ""
                content = (
                    f"To: {t_str}{backslash_n}"
                    + (f"CC: {cc_str}{backslash_n}" if cc_str else "")
                    + (f"BCC: {bcc_str}{backslash_n}" if bcc_str else "")
                    + f"Instruction: {data['instruction']}{backslash_n}"
                    + f"Language Tone: {data['language_tone']}{backslash_n}"
                    + f"Length: {data['length']}{backslash_n}"
                )
                history.append({"role": "user", "content": content})

        return history

    @staticmethod
    def create_chat(oauth: Oauth):
        """Start a new Chat record in DB."""
        chat = Chat(user_id=current_user.id, name="New Chat", oauth_id=oauth.id)
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def _split_subject_body(text: str):
        """Extract Subject and Body from AI-generated text."""
        if "Body:" in text:
            parts = text.split("Subject: ")[1].split("Body:")
        else:
            parts = text.split("Subject: ")[1].split("\n", 1)
        subj = parts[0].strip()
        body = parts[1].lstrip("\n") if len(parts) > 1 else ""
        return subj, body

    @staticmethod
    def generate_email(contacts, instruction, language_tone, length, oauth, ai="openai"):
        """Main endpoint: generate a new email draft."""
        # 1) create DB chat record
        chat = ChatAssistant.create_chat(oauth)

        # 2) bucket contacts
        to, cc, bcc = ChatAssistant.seperate_contacts(contacts)

        # 3) prepare metadata
        email_length = LENGTH_MAP.get(length, "Unknown")
        input_data = {
            "contacts": contacts,
            "instruction": instruction,
            "language_tone": language_tone,
            "length": email_length
        }

        # 4) format prompt pieces
        to_block  = ChatAssistant.format_contact(to,  "To")
        cc_block  = ChatAssistant.format_contact(cc,  "Cc")
        bcc_block = ChatAssistant.format_contact(bcc, "Bcc")

        length_str = f"Email Length: {email_length}"
        instr_str  = f"Instruction: {instruction}"
        tone_str   = f"Language Tone: {language_tone}"

        user = current_user
        sender_block = (
            f"Full Name: {oauth.first_name} {oauth.last_name or ''}{backslash_n}"
            f"Email: {oauth.email}{backslash_n}"
            + (f"Phone: {user.phone_code} {user.phone_number}{backslash_n}"
               if user.phone_code and user.phone_number else "")
            + (f"Company: {user.company}, {user.work_title}{backslash_n}"
               if user.company and user.work_title else "")
            + (f"College: {user.college}, {user.major}{backslash_n}"
               if user.college and user.major else "")
        )

        user_prompt = (
            sender_block
            + f"Recipient(s) Details:{backslash_n}"
            + (to_block or "")
            + (f"{cc_block}{backslash_n}" if cc_block else "")
            + (f"{bcc_block}{backslash_n}" if bcc_block else "")
            + f"Email Details:{backslash_n}"
            + f"Instruction: {instruction}{backslash_n}"
            + f"Language Tone: {language_tone}{backslash_n}"
            + f"Email Length: {LENGTH_MAP.get(length, 'Unknown')}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        # 5) call AI
        if ai == "openai":
            resp = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            gen_text = resp.choices[0].message.content
        else:
            resp = workersai.chat(messages)
            if not resp.get("success", False):
                err = resp.get("error", [])
                if err and err[0].get("message") == "Rate limited":
                    abort(400, "Rate limited. Please try again later.")
                abort(400, "Error generating email")
            gen_text = resp["result"]["response"]

        # 6) parse and persist
        subject, body = ChatAssistant._split_subject_body(gen_text)
        response_data = {"subject": subject.strip(), "body": body.strip()}

        chat.name = subject
        db.session.add(
            ChatMessages(
                user_id=current_user.id,
                chat_id=chat.id,
                data=fernet.encrypt(json.dumps(input_data).encode()).decode(),
                chat_type="user"
            )
        )
        db.session.add(
            ChatMessages(
                user_id=current_user.id,
                chat_id=chat.id,
                data=fernet.encrypt(json.dumps(response_data).encode()).decode(),
                chat_type="assistant"
            )
        )
        db.session.commit()

        return make_response(
            jsonify(
                chat_id=chat.id,
                assistant_message_id=ChatMessages.query.filter_by(chat_id=chat.id, chat_type="assistant").order_by(ChatMessages.id.desc()).first().id,
                user_message_id=ChatMessages.query.filter_by(chat_id=chat.id, chat_type="user").order_by(ChatMessages.id.desc()).first().id,
                contacts=contacts,
                user={
                    "id": user.id,
                    "first_name": oauth.first_name,
                    "last_name": oauth.last_name,
                    "email": oauth.email,
                    "phone_code": user.phone_code,
                    "phone_number": user.phone_number,
                    "company": user.company,
                    "work_title": user.work_title,
                    "college": user.college,
                    "major": user.major,
                },
                input=input_data,
                output=response_data,
            ),
            200,
        )

    @staticmethod
    def modify_email(chat_id, contacts, instruction, language_tone, length, ai="openai"):
        """Modify an existing email draft in a chat thread."""
        chat  = Chat.query.get(chat_id) or abort(404, "Chat not found")
        oauth = Oauth.query.get(chat.oauth_id) or abort(404, "Email Authentication not found")

        to, cc, bcc = ChatAssistant.seperate_contacts(contacts)
        email_length = LENGTH_MAP.get(length, "Unknown")
        input_data = {
            "contacts": contacts,
            "instruction": instruction,
            "language_tone": language_tone,
            "length": email_length
        }

        # Build prompt similar to generate_email, but include previous assistant message
        history = ChatAssistant.get_chat_history(chat_id)
        prev = next((m for m in history[::-1] if m["role"] == "assistant"), None)
        if not prev:
            abort(400, "No previous email to modify")

        prev_subject, prev_body = ChatAssistant._split_subject_body(prev["content"])
        modify_block = (
            f"Previous Email:{backslash_n}"
            f"Subject: {prev_subject}{backslash_n}"
            f"Body: {prev_body}{backslash_n}"
            f"Modify per instruction: {instruction}{backslash_n}"
        )

        # Reuse user_prompt from above
        email_to  = ChatAssistant.format_contact(to, "To")
        email_cc  = ChatAssistant.format_contact(cc, "Cc")
        email_bcc = ChatAssistant.format_contact(bcc, "Bcc")

        sender_block = (
            f"Full Name: {oauth.first_name} {oauth.last_name or ''}{backslash_n}"
            f"Email: {oauth.email}{backslash_n}"
        )

        user_prompt = (
            f"{sender_block}"
            f"{modify_block}"
        )

        messages = [{"role": "system",  "content": system_prompt}] + history + [{"role": "user", "content": user_prompt}]

        # Call AI
        if ai == "openai":
            resp = openai.chat.completions.create(model=model, messages=messages, temperature=temperature)
            gen_text = resp.choices[0].message.content
        else:
            resp = workersai.chat(messages)
            if not resp.get("success", False):
                err = resp.get("error", [])
                if err and err[0].get("message") == "Rate limited":
                    abort(400, "Rate limited. Please try again later.")
                abort(400, "Error generating email")
            gen_text = resp["result"]["response"]

        # Parse & save
        subject, body = ChatAssistant._split_subject_body(gen_text)
        response_data = {"subject": subject.strip(), "body": body.strip()}

        db.session.add(
            ChatMessages(
                user_id=current_user.id,
                chat_id=chat.id,
                data=fernet.encrypt(json.dumps(input_data).encode()).decode(),
                chat_type="user"
            )
        )
        db.session.add(
            ChatMessages(
                user_id=current_user.id,
                chat_id=chat.id,
                data=fernet.encrypt(json.dumps(response_data).encode()).decode(),
                chat_type="assistant"
            )
        )
        chat.name = subject
        db.session.commit()

        return make_response(jsonify(
            chat_id=chat.id,
            contacts=contacts,
            assistant_message_id=ChatMessages.query.filter_by(chat_id=chat.id, chat_type="assistant").order_by(ChatMessages.id.desc()).first().id,
            user_message_id=ChatMessages.query.filter_by(chat_id=chat.id, chat_type="user").order_by(ChatMessages.id.desc()).first().id,
            user={
                "id": current_user.id,
                "first_name": oauth.first_name,
                "last_name": oauth.last_name,
                "email": oauth.email,
                "phone_code": current_user.phone_code,
                "phone_number": current_user.phone_number,
                "company": current_user.company,
                "work_title": current_user.work_title,
                "college": current_user.college,
                "major": current_user.major,
            },
            input=input_data,
            output=response_data
        ), 200)

    @staticmethod
    def send_email(contacts, subject, body, chat_id, oauth_id):
        """Send the last generated email via the user’s OAuth credentials."""
        chat = Chat.query.get(chat_id) or abort(404, "Chat not found")
        if chat.user_id != current_user.id:
            abort(403, "Not authorized")
        if chat.is_sent:
            abort(400, "Email already sent")

        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first() or abort(404, "Email Authentication not found")
        if oauth_id != chat.oauth_id:
            chat.oauth_id = oauth_id
            db.session.commit()

        to, cc, bcc = ChatAssistant.seperate_contacts(contacts)
        to_emails  = [c["email"] for c in to]
        cc_emails  = [c["email"] for c in cc]  if cc else None
        bcc_emails = [c["email"] for c in bcc] if bcc else None

        # Decrypt OAuth data
        data = json.loads(fernet.decrypt(oauth.data.encode()).decode())
        sender = f"{oauth.first_name} {oauth.last_name or ''} <{oauth.email}>"
        rendered = render_template("email-template.html", body=body, watermark=True)

        if oauth.service == "google":
            client = Google(data)
            success = client.send_email(sender=sender, to=to_emails, subject=subject, message=rendered, cc=cc_emails, bcc=bcc_emails)
        elif oauth.service == "microsoft":
            client = Microsoft(data)
            success = client.send_email(sender=sender, to=to_emails, subject=subject, body=rendered, cc=cc_emails, bcc=bcc_emails)
        else:
            # Fallback SMTP or other
            success = False

        if success:
            chat.is_sent = True
            chat.sent_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def paraphrase_text(text, ai="openai"):
        """Have the AI paraphrase a block of text."""
        messages = [
            {"role": "system", "content": (
                "You are a simple paraphraser. Rephrase the input text while keeping its meaning intact and short. "
                "Your response should be concise and directly related to the original input. Do not add unrelated content, "
                "instructions, or prompts. Avoid including anything such as \"here is the rephrased text\" or placeholders like [your name]."
            )},
            {"role": "user", "content": text}
        ]
        if ai == "openai":
            resp = openai.chat.completions.create(model=model, messages=messages, temperature=temperature)
            gen = resp.choices[0].message.content
        else:
            resp = workersai.chat(messages)
            if not resp.get("success", False):
                err = resp.get("error", [])
                if err and err[0].get("message") == "Rate limited":
                    abort(400, "Rate limited. Please try again later.")
                abort(400, "Error generating paraphrase")
            gen = resp["result"]["response"]

        # Preserve original ending punctuation
        punct = re.search(r"[\W_]*$", text)
        gen = re.sub(r"[\W_]*$", "", gen) + (punct.group() if punct else "")
        return gen

    @staticmethod
    def smart_reply(subject, body, sender, instruction, oauth, ai="openai"):
        """Generate a smart reply to an incoming email."""
        text = f"Subject: {subject}{backslash_n}Body: {Email.extract_text_from_html(body)}"
        user_prompt = (
            f"My Details:{backslash_n}"
            f"Full Name: {oauth.first_name} {oauth.last_name or ''}{backslash_n}"
            f"Email: {oauth.email}{backslash_n}"
            f"Recipient(s) Details: {sender}{backslash_n}"
            f"Instruction: {instruction}"
        )

        messages = [
            {"role": "system", "content": (
                "You are an email generator. Based on the provided details, generate a concise and relevant draft reply. "
                "Ensure the reply aligns with the original email’s tone and context. Include appropriate greetings (e.g., \"Dear,\" \"Hello\") "
                "and a closing signature (e.g., \"Best regards,\" \"Sincerely\") based on the tone. Do not include introductory phrases, placeholders "
                "(e.g., \"[your name]\"), unrelated content, or a subject line. Focus solely on generating the reply content. "
                f"Today's date is {today_date_time}."
            )},
            {"role": "user", "content": text},
            {"role": "user", "content": user_prompt}
        ]

        if ai == "openai":
            resp = openai.chat.completions.create(model=model, messages=messages, temperature=temperature)
            return resp.choices[0].message.content
        else:
            resp = workersai.chat(messages)
            if not resp.get("success", False):
                err = resp.get("error", [])
                if err and err[0].get("message") == "Rate limited":
                    abort(400, "Rate limited. Please try again later.")
                abort(400, "Error generating smart reply")
            return resp["result"]["response"]
