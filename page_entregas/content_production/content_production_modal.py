import logging
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from common.models import ContentProduction
from common.database import engine
from streamlit_modal import Modal

# Function to open the content production modal
def modal_content_production_open(cliente_id):
    logging.debug(f"modal_content_production_open() called for client ID {cliente_id}")

    # Initialize the modal
    modal = Modal("Add New Content Production Meeting", key="add-content-production-modal", max_width=800)

    # Check if the modal should be open
    if st.session_state.get("open_content_modal", False):
        modal.open()
        logging.debug("Content Production Modal opened.")

        with modal.container():
            with st.form(key='content_production_form'):
                meeting_date = st.date_input("Meeting Date", value=datetime.today())
                meeting_subject = st.text_input("Subject")
                notes = st.text_area("Notes")
                submit_button = st.form_submit_button(label='Save')

                if submit_button:
                    if meeting_subject:  # Ensure the subject is not empty
                        save_new_content_production(cliente_id, meeting_date, meeting_subject, notes)
                        logging.info(f"Content Production meeting saved for client ID {cliente_id}")

                        st.success("Content Production meeting added successfully!")
                        # Update the state and close the modal
                        st.session_state["open_content_modal"] = False
                        # No need to call st.experimental_rerun()
                    else:
                        st.error("The Subject field cannot be empty.")
    else:
        # Do not execute the modal content if it's not open
        pass

# Function to save the new content production meeting to the database
def save_new_content_production(cliente_id, meeting_date, meeting_subject, notes):
    try:
        with Session(bind=engine) as session:
            new_entry = ContentProduction(
                client_id=cliente_id,
                meeting_date=meeting_date,
                meeting_subject=meeting_subject,
                notes=notes
            )
            session.add(new_entry)
            session.commit()
            logging.info(f"New Content Production meeting saved to the database for client ID {cliente_id}.")
    except Exception as e:
        logging.error(f"Error saving the Content Production meeting: {e}")
        st.error(f"Error saving the Content Production meeting: {e}")
