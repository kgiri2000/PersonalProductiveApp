import streamlit as st
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime

# Google Drive Authentication using Streamlit Secrets
@st.cache_resource
def authenticate_drive():
    """
    Authenticate with Google Drive using credentials stored in Streamlit Secrets.
    """
    gauth = GoogleAuth()

    # Use credentials from Streamlit secrets
    client_id = st.secrets["google_drive"]["client_id"]
    client_secret = st.secrets["google_drive"]["client_secret"]
    access_token = st.secrets["google_drive"]["access_token"]

    # Load credentials from secrets
    gauth.ClientId = client_id
    gauth.ClientSecret = client_secret
    gauth.AccessToken = access_token

    if not gauth.credentials:
        gauth.LocalWebserverAuth()  # Authenticate if not saved
    elif gauth.access_token_expired:
        gauth.Refresh()  # Refresh credentials if expired
    else:
        gauth.Authorize()  # Authorize saved credentials

    gauth.SaveCredentialsFile("mycreds.txt")  # Save credentials for future use
    return GoogleDrive(gauth)

# Function to create a folder in Google Drive
def create_drive_folder(folder_name, parent_folder_id=None):
    """
    Creates a folder in Google Drive.
    """
    folder_metadata = {
        "title": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [{"id": parent_folder_id}] if parent_folder_id else []
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder["id"]

# Function to get or create a user folder
def get_user_folder(username):
    """
    Retrieves existing user folder or creates one if not found.
    """
    file_list = drive.ListFile(
        {"q": f"mimeType='application/vnd.google-apps.folder' and title='{username}'"}
    ).GetList()
    if file_list:
        return file_list[0]["id"]
    return create_drive_folder(username)

# Function to get or create a date subfolder
def get_date_folder(username_folder_id, date_str):
    """
    Retrieves existing date subfolder or creates one if not found.
    """
    file_list = drive.ListFile(
        {
            "q": f"'{username_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and title='{date_str}'"
        }
    ).GetList()
    if file_list:
        return file_list[0]["id"]
    return create_drive_folder(date_str, parent_folder_id=username_folder_id)

# Function to save a note to Google Drive
def save_note(folder_id, note_content):
    """
    Saves the note content to Google Drive as a JSON file.
    """
    note_file = drive.CreateFile({"parents": [{"id": folder_id}], "title": "note.json"})
    note_file.SetContentString(json.dumps(note_content))
    note_file.Upload()

# Function to read a note from Google Drive
def read_note(folder_id):
    """
    Retrieves the note content from Google Drive.
    """
    file_list = drive.ListFile({"q": f"'{folder_id}' in parents and title='note.json'"}).GetList()
    if file_list:
        note_file = file_list[0]
        note_file.FetchContent()
        return json.loads(note_file.content.read().decode("utf-8"))
    return None

# Streamlit App - Main UI and Logic
def main():
    """
    Main function to run the Streamlit app. Manages user authentication, folder management,
    note creation, and note display.
    """
    st.title("Productivity Website with Persistent Notes")
    
    # Home Page: Log in or show existing session
    if "username" not in st.session_state:
        # If not logged in, ask for username
        username = st.text_input("Enter your username:")
        if(username != "kgiri" and username != "rgiri"):  # Validation example
            st.warning("Wrong user Name")
            st.stop()
        if st.button("Log In"):
            if username:
                # Store the username in session state and rerun the app
                st.session_state["username"] = username
                st.rerun()
    else:
        username = st.session_state["username"]
        st.write(f"Welcome, **{username}**!")
        
        # Get or create user folder
        user_folder_id = get_user_folder(username)

        # Select date
        selected_date = st.date_input("Select a date:")
        if selected_date:
            date_str = selected_date.strftime("%Y-%m-%d")
            date_folder_id = get_date_folder(user_folder_id, date_str)

            # Note management
            options = ["Create Note", "Open Note"]
            action = st.radio("Choose an option:", options)

            if action == "Create Note":
                # Prompt the user for input
                how_was_your_day = st.text_area("How was your day?")
                unique_thing_learned = st.text_area("Unique thing you learned today")
                quote_of_the_day = st.text_area("Motivation/Quote of the Day/Fact")

                # Save the note as a JSON file
                if st.button("Save Note"):
                    if how_was_your_day and unique_thing_learned and quote_of_the_day:
                        note_content = {
                            "how_was_your_day": how_was_your_day,
                            "unique_thing_learned": unique_thing_learned,
                            "quote_of_the_day": quote_of_the_day
                        }
                        save_note(date_folder_id, note_content)
                        st.success("Note saved successfully!")
                    else:
                        st.warning("Please fill in all sections before saving.")
            
            elif action == "Open Note":
                note_content = read_note(date_folder_id)
                if note_content:
                    # Display the note sections separately
                    st.write(f"**How was your day?**: {note_content['how_was_your_day']}")
                    st.write(f"**Unique thing you learned today**: {note_content['unique_thing_learned']}")
                    st.write(f"**Motivation/Quote of the day**: {note_content['quote_of_the_day']}")
                else:
                    st.warning("No note exists for this date.")

if __name__ == "__main__":
    # Authenticate with Google Drive
    drive = authenticate_drive()
    main()
