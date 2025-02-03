# jira_manager module
# Module holds the class => JiraManager - manages JIRA ticket interface
# Class responsible for all JIRA related interactions including ticket searching, data pull, file attaching, comment
# posting and field updating.
#
from jira import JIRA
from datetime import date


class JiraManager(object):
    def __init__(self, url, jira_token):
        self.tickets = []
        self.jira = JIRA(url, basic_auth=jira_token)
        self.comments = ""
        self.title = ""
        self.today_date = date.today().strftime('%Y-%m-%d')     # format required for Jira date field
        self.api_results_fail_alert = 'Could not find any api results for this run.'
        self.ticket_transitionid = '471'    # 'Complete' w/ Rev-Rec

    # Searches Jira for all tickets that match the parent ticket query criteria
    #
    def find_tickets(self, search_type, parent_ticket, ticket_type, ticket_status, summary_text):
        # Query to find corresponding Jira Tickets
        self.tickets = []
        if search_type == 'parent':
            jql_query = "Project in (CAM) AND Type = " + ticket_type + " AND Status in " + ticket_status \
                        + " AND Summary ~ " + summary_text
        else:       # this is the jql for the child ticket search
            jql_query = "Parent in (" + parent_ticket.key + ") AND Status in " + ticket_status

        self.tickets = self.jira.search_issues(jql_query, maxResults=500)

        if len(self.tickets) > 0:
            return self.tickets
        else:
            return None

    # Retrieves the required data from parent ticket to populate email
    #
    def information_pull(self, ticket):
        ticket = self.jira.issue(ticket.key)
        # find and return the title for the ticket and all the comments (in dict form)
        self.comments = ticket.fields.comment.comments
        title = str(ticket.fields.parent.fields.summary)
        #print("Is this an ascii string?: {}".format(self.is_ascii(title)))
        self.title = ''.join(char for char in title if char.isalnum())
        #print("{}".format(self.title))
        return self.comments, self.title

    # Add a comment to ticket informing of no api results
    #
    def add_no_results_comment(self, ticket):
        cam_ticket = self.jira.issue(ticket.key)
        reporter = cam_ticket.fields.reporter.key
        message = """{api_results_fail_comment}
                  """.format(reporter, api_results_fail_comment=self.api_results_fail_alert)
        self.jira.add_comment(issue=cam_ticket, body=message)

    # Add a text file copy of email as an attachment to ticket
    #
    def add_attachment(self, ticket, email_subject, attachment):
        email_file_name = "{}.txt.png".format(email_subject)
        self.jira.add_attachment(issue=ticket, attachment=attachment,
                                 filename=email_file_name)
        email_file_name = "{}.txt".format(email_subject)
        self.jira.add_attachment(issue=ticket, attachment=attachment,
                                 filename=email_file_name)

    # Update the field 'Due Date' in the ticket to today's date
    #
    def update_field_value(self, ticket):
        ticket.fields.due_date = self.today_date
        ticket.update(fields={'duedate': ticket.fields.due_date})

    # Transition the ticket status field to 'Complete'
    #
    def progress_ticket(self, ticket):
        ticket = self.jira.issue(ticket.key)
        self.jira.transition_issue(ticket, self.ticket_transitionid)

    # Ends the current JIRA session
    #
    def kill_session(self):
        self.jira.kill_session()

    # Test string for non-ascii characters
    #
    @staticmethod
    def is_ascii(text):
        # first test if a str, if true, use encode()
        if isinstance(text, str):
            try:
                text.encode('ascii')
            # if cannot encode then not ascii, return false
            except UnicodeEncodeError:
                return False
        # if not a str then a bytes sequence, so use decode()
        else:
            try:
                text.decode('ascii')
            # of cannot decode than not ascii, return false
            except UnicodeDecodeError:
                return False
        # if either decoded or encoded successfully,  than it is an ascii, return true
        return True

    # Clean any non-ascii chars from string
    #
    @staticmethod
    def clean_ascii(text):
        text.encode('ascii', errors='ignore').decode()
        return text
