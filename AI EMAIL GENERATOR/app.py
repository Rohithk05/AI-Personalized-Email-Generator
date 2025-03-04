import streamlit as st
from transformers import pipeline
import google.generativeai as genai
import os
from dotenv import load_dotenv
import utils
from streamlit_option_menu import option_menu
from fastapi import FastAPI, File, UploadFile
from pathlib import Path
import uvicorn
import requests
# --- Load environment variables ---
load_dotenv()
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-8b')  # Or 'gemini-pro-vision' for image input
# --- FastAPI Setup for File Uploads ---
#Separate FastAPI instance for handling file uploads
upload_app = FastAPI()

@upload_app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    # Create the attachments directory if it doesn't exist
    attachments_dir = Path("attachments")
    attachments_dir.mkdir(exist_ok=True)

    file_location = attachments_dir / file.filename
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"filename": file.filename, "filepath": str(file_location)}

# --- Streamlit UI ---
def main():
     # Sidebar for Navigation
    with st.sidebar:
        selected = option_menu(
            "Email Generator",
            ["Compose Email", "Email Preview", "Settings"],
            icons=["pencil-fill", "eye-fill", "gear-fill"],
            menu_icon="envelope-fill",
            default_index=0,
        )
    if selected == "Compose Email":
      compose_email_page()
    elif selected == "Email Preview":
      email_preview_page()
    elif selected == "Settings":
        settings_page()


# --- Page Functions ---
def compose_email_page():
    st.title("Compose New Email")

    # --- User Input Form ---
    sender_email = st.text_input("Your Email Address")
    receiver_name = st.text_input("Recipient's Name")
    receiver_email = st.text_input("Recipient's Email Address")

    email_types = [
        "Professional", "Feedback", "Sick Leave", "Personal", "Survey",
        "Confirmation", "Invitation", "Other"
    ]
    email_type = st.selectbox("Email Type", email_types)

    if email_type == "Other":
        email_type = st.text_input("Enter Email Type")

    tones = [
        "Formal", "Friendly", "Encouraging", "Neutral", "Professional",
        "Casual", "Optimistic", "Convincing", "Urgent", "Appreciative"
    ]
    tone = st.selectbox("Email Tone", tones)

    email_subject = st.text_input("Email Subject")  # Add a subject input
    email_body_prompt = st.text_area("Describe the email content you want to generate:", height=150)


    # --- File Upload Section ---
    uploaded_files = st.file_uploader("Attach files (optional)", type=["pdf", "docx", "txt", "jpg", "png", "mp4"], accept_multiple_files=True)
    # --- Generate Email Button ---
    if st.button("Generate Email"):
        if not all([sender_email, receiver_email, email_type, tone, email_body_prompt, email_subject]): #and subject
            st.warning("Please fill in all required fields.")
            return
            # --- Construct Prompt for Gemini Pro ---
        prompt = f"""
        Write an email with the following specifications:

        Type: {email_type}
        Tone: {tone}
        Subject: {email_subject}  # Include subject in prompt
        Recipient Name: {receiver_name}
        Sender : {sender_email}
        Main Content/Purpose: {email_body_prompt}
        """
        # --- Upload files to FastAPI endpoint ---
        attachment_paths = []
        if uploaded_files:
          for uploaded_file in uploaded_files:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post("http://localhost:8001/uploadfile/", files=files) # Assuming FastAPI runs on port 8001
            if response.status_code == 200:
                attachment_paths.append(response.json()["filepath"])
            else:
                st.error(f"Error uploading file: {uploaded_file.name}")


        # --- Call Gemini Pro API ---
        try:
            #response = model.generate_content(prompt)
            #email_content = response.text
              # Check if there are images to include
            if any(file.type.startswith('image/') for file in uploaded_files) :
              #Using Gemini Pro Vision for images

              image_parts = []
              for uploaded_file in uploaded_files:
                if uploaded_file.type.startswith('image/'):
                  image_parts.append({
                      "mime_type": uploaded_file.type,
                      "data": uploaded_file.getvalue()
                  })
              prompt_parts = [prompt, *image_parts]
              response = model.generate_content(prompt_parts) #no prompt here , pass the prompt parts
              email_content = response.text

            else:
              response = model.generate_content(prompt) #if there are no image parts then pass the prompt
              email_content = response.text


            st.session_state.generated_email = email_content  # Store in session state
            st.session_state.attachment_paths = attachment_paths
            st.session_state.sender_email = sender_email
            st.session_state.receiver_email = receiver_email
            st.success("Email generated successfully!  Go to the 'Email Preview' tab.")


        except Exception as e:
            st.error(f"An error occurred: {e}")

# Email preview and operations
def email_preview_page():
    st.title("Email Preview")
    if "generated_email" in st.session_state:
        # --- Email Display ---
        st.subheader("Generated Email:")
        st.write(st.session_state.generated_email)

        # --- Read Aloud ---
        if st.button("Read Aloud"):
            utils.text_to_speech(st.session_state.generated_email)

        # --- Translation ---
        target_language = st.selectbox("Translate to:", ["", "Spanish", "French", "German", "Chinese", "Japanese","Telugu","Hindi"] + sorted(utils.get_supported_languages()))  # Add more languages
        if target_language:
            translated_text = utils.translate_text(st.session_state.generated_email, target_language)
            st.subheader(f"Translated Email ({target_language}):")
            st.write(translated_text)

        # --- Send Email ---
        if st.button("Send Email"):
          if "sender_email" not in st.session_state or "receiver_email" not in st.session_state:
            st.error("Sender or receiver email not found. Please generate the email again.")
            return
          with st.spinner("Sending email..."):
            try:
                  if "attachment_paths" in st.session_state:  # Check if attachments exist
                      result = utils.send_email(
                          st.session_state.sender_email,
                          st.session_state.receiver_email,
                          "Generated Email Subject",  # Use a consistent subject or get from input
                          st.session_state.generated_email,
                          st.session_state.attachment_paths  # Pass attachments
                      )
                  else:
                    result = utils.send_email(
                          st.session_state.sender_email,
                          st.session_state.receiver_email,
                          "Generated Email Subject",  # Use a consistent subject or get from input
                          st.session_state.generated_email,
                      )


                  if result:
                      st.success("Email sent successfully!")
                  else:
                      st.error("Failed to send email.")
            except Exception as e:
                st.error(f"An error occurred while sending: {e}")
    else:
        st.info("Please generate an email first.")

#Email settings
def settings_page():
    st.title("Settings")
    st.write("Coming soon...")  # Placeholder for future settings (e.g., default tone, signature)

if __name__ == "__main__":
    main()
    # Run FastAPI alongside Streamlit (using threading or a separate process)
    # This is a basic example; consider using a process manager like Gunicorn for production
    import threading
    def run_fastapi():
        uvicorn.run(upload_app, host="0.0.0.0", port=8001)

    thread = threading.Thread(target=run_fastapi)
    thread.start()