# email module
# Module holds the class => EmailManager - manages the email creation and the smtp interface
# Class responsible for all email related management
#
from smtplib import SMTP
from email.message import EmailMessage


class EmailManager(object):
    def __init__(self, pixel, subject, to_address, from_address):
        self.pixel = pixel
        self.msg = ""
        self.subj = subject
        self.to_address = to_address
        self.from_address = from_address

    # Create the email in a text format then send via smtp, finally save the email as a StringIO file and return
    #
    def cm_emailer(self, results_text):
        # Simple Text Email
        self.msg = EmailMessage()
        self.msg['Subject'] = self.subj
        self.msg['From'] = self.from_address
        self.msg['To'] = self.to_address

        # Message Text
        self.msg.set_content(results_text)

        # Send Email
        with SMTP('mailhost.valkyrie.net') as smtp:
            smtp.send_message(self.msg)

        return self.msg
