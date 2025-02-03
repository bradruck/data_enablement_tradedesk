**Description -**

The Data Enhancement Trade Desk Attachment for Finance is an automation to find Data License tickets each week that
have finished post processing and require a simple email attachment to the jira ticket before the job can be closed
out and revenue recognition can be alerted for finance billing purposes. The automation starts by finding each parent
ticket that spawns a weekly child ticket.  When the child ticket has been identified, the comments section of that
ticket is searched for an api returned count. This count is then copied and entered into an email message as the text
body. The email is then attached as a text file to the Jira ticket.  The automation then updates the 'Due' field to
today's date and finally transitions the status to "Complete' with rev-rec. Finally, a json file with a dictionary of
all the api returned counts is created and placed within a directory in the designated log folder on zfs
Operations_limited. The automation is scheduled to run Wednesday, Thursday and Friday each week at 2pm.

**Application Information -**

Required modules: <ul>
                  <li>main.py,
                  <li>trade_desk_attachment_manager.py,
                  <li>jira_manager.py,
                  <li>email_manager.py,
                  <li>config.ini
                  </ul>

Location:         <ul>
                  <li>Deployment -> //prd-use1a-pr-34-ci-operations-01/home/bradley.ruck/Projects
                                                                                    /data_enablement_trade_desk_attach/
                  <li>Scheduled to run once a day, triggered by ActiveBatch-V11 under File/Plan -> DE_TDD_Attach
                  </ul>

Source Code:      <ul>
                  <li>//gitlab.oracledatacloud.com/odc-operations/DE_TradeDesk/
                  </ul>

LogFile Location: <ul>
                  <li>//zfs1/Operations_limited/Data_Enablement/Data_License_TTD/TTDLogs/
                  </ul>
                  
JsonFile Location:<ul>
                  <li>//zfs1/Operations_limited/Data_Enablement/Data_License_TTD/TTDLogs/Results/
                  </ul>

**Contact Information -**

Primary Users:    <ul>
                  <li>Data Enablement
                  </ul>

Lead Customer(s): <ul>
                  <li>Zack Batt(zack.batt@oracle.com)
                  </ul>

Lead Developer:   <ul>
                  <li>Bradley Ruck (bradley.ruck@oracle.com)
                  </ul>

Date Launched:    <ul>
                  <li>July, 2018
                  </ul>