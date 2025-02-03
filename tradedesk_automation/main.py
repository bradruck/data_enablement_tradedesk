# Data Enablement - Data License, Trade Desk Attachment for Finance

# Description -
# The Data Enhancement Trade Desk Attachment for Finance is an automation to find Data License tickets each week that
# have finished post processing and require a simple email attachment to the jira ticket before the job can be closed
# out and revenue recognition can be alerted for finance billing purposes. The automation starts by finding each parent
# ticket that spawns a weekly child ticket.  When the child ticket(s) has been identified, the comments section of that
# ticket is searched for an api returned count. This count is then copied and entered into an email message as the text
# body. The email is then attached as a text file to the Jira ticket.  The automation then updates the 'Due' field to
# today's date and finally transitions the status to "Complete' with rev-rec. Finally, a json file with a dictionary of
# all the api returned counts is created and placed within a directory in the designated log folder on zfs
# Operations_limited. The automation is scheduled to run Wednesday, Thursday and Friday each week at 2pm.
#
# Application Information -
# Required modules:     main.py,
#                       trade_desk_attachment_manager.py,
#                       jira_manager.py,
#                       email_manager.py,
#                       config.ini
# Deployed Location:    //prd-use1a-pr-34-ci-operations-01/home/bradley.ruck/Projects/data_enablement_trade_desk_attach/
# ActiveBatch Trigger:  //prd-09-abjs-01 (V11)/'Jobs, Folders & Plans'/Operations/Report/DE_TDD_Attach/DE_TDD_WedThurFri
# Source Code:          //gitlab.oracledatacloud.com/odc-operations/DE_TradeDesk/
# LogFile Location:     //zfs1/Operations_limited/Data_Enablement/Data_License_TTD/TTDLogs/
# JsonFile Location:    //zfs1/Operations_limited/Data_Enablement/Data_License_TTD/TTDLogs/Results/
#
# Contact Information -
# Primary Users:        Data Enablement
# Lead Customer:        Zack Batt(zack.batt@oracle.com)
# Lead Developer:       Bradley Ruck (bradley.ruck@oracle.com)
# Date Launched:        July, 2018
# Date Updated:         August, 2020

# main module
# Responsible for reading in the basic configurations settings, creating the log file, and creating and launching
# The Trade Desk Attachment Manager (TTD-AM), finally it launches the purge_files method to remove log files that
# are older than a prescribed retention period. A console logger option is offered via keyboard input for development
# purposes when the main.py script is invoked. For production, import main as a module and launch the main function
# as main.main(), which uses 'n' as the default input to the the console logger run option.
#
from datetime import datetime, timedelta
import os
import configparser
import logging
from VaultClient3 import VaultClient3 as VaultClient

from trade_desk_attachment_manager import TTDAttachmentManager


# Define a console logger for development purposes
#
def console_logger():
    # define Handler that writes DEBUG or higher messages to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a simple format for console use
    formatter = logging.Formatter('%(levelname)-7s: %(name)-30s: %(threadName)-12s: %(message)s')
    console.setFormatter(formatter)
    # add the Handler to the root logger
    logging.getLogger('').addHandler(console)


def main(con_opt='n'):
    today_date = (datetime.now() - timedelta(hours=6)).strftime('%Y%m%d-%H%M%S')

    # create a configparser object and open in read mode
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Vault Client Object
    VC_Obj = VaultClient("prod")
    pd = VC_Obj.VaultSecret('jira', str(config.get('Jira', 'authorization')))

    # create a dictionary of configuration parameters
    config_params = {
        "jira_url":             config.get('Jira', 'url'),
        "jira_token":           tuple([config.get('Jira', 'authorization'), pd]),
        "jql_parent_type":      config.get('Jira', 'parent_type'),
        "jql_parent_status":    config.get('Jira', 'parent_status'),
        "jql_parent_text":      config.get('Jira', 'parent_text'),
        "jql_child_status":     config.get('Jira', 'child_status'),
        "results_json_path":    config.get('ResultsFile', 'path'),
        "results_json_name":    config.get('Project Details', 'app_name'),
        "email_to":             config.get('Email', 'to'),
        "email_from":           config.get('Email', 'from')
    }

    # logfile path to point to the Operations_limited drive on zfs
    purge_days = config.get('LogFile', 'retention_days')
    log_file_path = config.get('LogFile', 'path')
    logfile_name = '{}{}_{}.log'.format(log_file_path, config.get('Project Details', 'app_name'), today_date)

    # check to see if log file already exits for the day to avoid duplicate execution
    if not os.path.isfile(logfile_name):
        logging.basicConfig(filename=logfile_name,
                            level=logging.INFO,
                            format='%(asctime)s: %(levelname)-7s: %(name)-30s: %(threadName)-12s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S')

        logger = logging.getLogger(__name__)

        # checks for console logger option, default value set to 'n' to not run in production
        if con_opt and con_opt in ['y', 'Y']:
            console_logger()

        logger.info("Process Start - The Trade Desk Email Attachment, Data Enablement - {}\n".format(today_date))

        # create TTD-AM object and launch the process manager
        ttd_attach = TTDAttachmentManager(config_params)
        ttd_attach.process_manager()

        # search logfile directory for old log files to purge
        ttd_attach.purge_files(purge_days, log_file_path)


if __name__ == '__main__':
    # prompt user for use of console logging -> for use in development not production
    ans = input("\nWould you like to enable a console logger for this run?\n Please enter y or n:\t")
    print()
    main(ans)
