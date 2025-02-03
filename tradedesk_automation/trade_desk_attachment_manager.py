# mobile_id_match_manager module
# Module holds the class => MobileIDMatchManager - manages the Mobile ID Matching Process
# Class responsible for overall program management
#
from datetime import datetime, timedelta
import time
import os
from io import StringIO
import json
import logging
from jira_manager import JiraManager
from email_manager import EmailManager

today_date = (datetime.now() - timedelta(hours=6)).strftime('%Y%m%d-%H%M%S')


class TTDAttachmentManager(object):
    def __init__(self, config_params):
        self.jira_url = config_params['jira_url']
        self.jira_token = config_params['jira_token']
        self.jira_pars = JiraManager(self.jira_url, self.jira_token)
        self.parent_jql_kwargs = {'parent_ticket': None,
                                  'ticket_type': config_params['jql_parent_type'],
                                  'ticket_status': config_params['jql_parent_status'],
                                  'summary_text': config_params['jql_parent_text']}
        self.jql_child_status = config_params['jql_child_status']
        self.results_json_path = config_params['results_json_path']
        self.results_json_name = config_params['results_json_name']
        self.email_to = config_params['email_to']
        self.email_from = config_params['email_from']
        self.results_file_name = '{}{}_{}.json'.format(self.results_json_path, self.results_json_name, today_date)
        self.parent_tickets = []
        self.child_tickets = []
        self.results_dict = {}
        self.logger = logging.getLogger(__name__)

    # Manages the overall automation
    #
    def process_manager(self):
        # pulls desired tickets running jql
        self.parent_tickets = self.jira_pars.find_tickets('parent', **self.parent_jql_kwargs)
        self.logger.info("{} ticket(s) were found.".format(len(self.parent_tickets)))
        self.logger.info(str([ticket.key for ticket in self.parent_tickets]) + "\n")

        # verifies that parent tickets were found that match the search criteria and logs parent ticket key,
        # then finds child ticket(s) and pulls issue information for email propagation
        if self.parent_tickets:
            for parent_ticket in self.parent_tickets:
                self.logger.info("Parent Ticket Number: {}".format(parent_ticket))

                # find the related active child ticket
                child_jql_kwargs = {'parent_ticket': parent_ticket, 'ticket_type': None,
                                    'ticket_status': self.jql_child_status, 'summary_text': None}
                child_tickets = self.jira_pars.find_tickets('child', **child_jql_kwargs)

                if child_tickets is not None:
                    # only one ticket in list, so eliminate the list data structure by removing the only ticket
                    #child_ticket = child_tickets.pop()
                    # small rewrite to allow for multiple child tickets per parent ticket in a single week
                    self.logger.info("Child Tickets: {}".format(str([ticket.key for ticket in self.child_tickets])
                                                                + "\n"))
                    for child_ticket in child_tickets:
                        self.logger.info("Child Ticket: {}".format(child_ticket.key))
                        # mine the child ticket for information
                        comments, title = self.jira_pars.information_pull(child_ticket)
                        # create the subject line for email population
                        email_subject = "{} {}".format(child_ticket.key, title)
                        # search comments for only the api returned counts
                        if comments is not None:
                            results_text, ticket_level_dict = self.comments_searcher(comments)
                            if results_text is not None:
                                # send results at email and attach text copy to ticket
                                attachment = self.emailer(child_ticket, email_subject, results_text)
                                self.ticket_manager(child_ticket, email_subject, attachment)
                                # save ticket level results dict into a run dict
                                self.results_dict[child_ticket.key] = ticket_level_dict
                            else:
                                self.ticket_manager(child_ticket, email_subject, None)
                else:
                    self.logger.warning("There are no child tickets.")
                self.logger.info("End of parent ticket thread\n")
        if self.results_dict:
            self.json_file_write()

    # Searches jira ticket 'comments' section for api returned counts
    #
    def comments_searcher(self, comments):
        # checks the comments for the api returned counts
        ticket_level_dict = {}
        for comment in comments:
            # return value for the comment with the key == 'body', split value into a list and check the first item
            results_text = comment.raw.get('body')
            if results_text.split('\n')[0] == 'TradeDesk API stats:':
                # add api returned results to a ticket level results dictionary
                ticket_level_dict[results_text.split('\n')[1].split(':')[0]] = results_text.split('\n')[1].split(':')[1]
                ticket_level_dict[results_text.split('\n')[2].split(':')[0]] = results_text.split('\n')[2].split(':')[1]
                self.logger.info("{}".format(' '.join(results_text.split('\n'))))
                return results_text, ticket_level_dict
        self.logger.warning("The api returned counts have not yet posted to the comments section of ticket.")
        return None, None

    # Confirm email, post as attachment to Jira ticket, 'Due' date field updated and transition to 'Complete' status
    #
    def ticket_manager(self, ticket, email_subject, result):
        if result is not None:
            try:
                self.jira_pars.add_attachment(ticket, email_subject, result)
                self.logger.info("A text of the email has been added as an attachment to Ticket {}".format(ticket.key))
            except Exception as e:
                self.logger.warning("There was a problem adding the email attachment to the ticket. {}".format(e))
            else:
                self.jira_pars.update_field_value(ticket)
                self.logger.info("A 'Due' date has been added to Ticket {}".format(ticket.key))
                self.jira_pars.progress_ticket(ticket)
                self.logger.info("Ticket {} has been transitioned to the 'Complete' status".format(ticket.key))
        else:
            self.jira_pars.add_no_results_comment(ticket)
            self.logger.warning("A ticket alert has been added as a comment to Ticket {}".format(ticket.key))

    # Creates the Email Manager instance, launches the emailer module and returns the sent email as a StringIO
    #
    def emailer(self, ticket, email_subject, results_text):
        cm_email = EmailManager(ticket, email_subject, self.email_to, self.email_from)
        try:
            msg_text = cm_email.cm_emailer(results_text)

        except Exception as e:
            self.logger.error = ("Email failed for ticket {} => {}".format(ticket.key, e))

        else:
            attachment = StringIO()
            # Convert email to StringIO
            message = bytes(msg_text).decode('utf-8')
            attachment.write(message)
            attachment.seek(0)
            self.logger.info("An email for ticket {} results has been sent.".format(ticket.key))
            return attachment

    # Writes the run data to a json file as a history repository and potential further processing
    #
    def json_file_write(self):
        try:
            # create json file for results repository, to be stored on zfs1/operations_mounted drive
            with open(self.results_file_name, 'w') as fp:
                json.dump(self.results_dict, fp, indent=4)
        except Exception as e:
            self.logger.error("There was a problem creating the json data file or posting it to "
                              "/zfs1/operations_limited => {}".format(e))
        else:
            self.logger.info("The results have been posted to: {}".format(self.results_file_name))

    # Checks the log directory for all files and removes those after a specified number of days
    #
    def purge_files(self, purge_days, purge_dir):
        try:
            self.logger.info("\n\t\tRemove {} days old files from the {} directory".format(purge_days, purge_dir))
            now = time.time()
            for file_purge in os.listdir(purge_dir):
                f_obs_path = os.path.join(purge_dir, file_purge)
                if os.stat(f_obs_path).st_mtime < now - int(purge_days) * 86400:
                    time_stamp = time.strptime(time.strftime('%Y-%m-%d %H:%M:%S',
                                                             time.localtime(os.stat(f_obs_path).st_mtime)),
                                               '%Y-%m-%d %H:%M:%S')
                    self.logger.info("Removing File [{}] with timestamp [{}]".format(f_obs_path, time_stamp))

                    os.remove(f_obs_path)

        except Exception as e:
            self.logger.error("{}".format(e))
