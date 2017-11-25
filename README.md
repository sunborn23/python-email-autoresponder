# Python Reply-To Autoreplier

Simple python script that connects to a mail server via IMAP and SMTP and replies to 
all emails in the inbox coming from a certain sender address using the included Reply-To field. 
Mails that have been replied to are deleted afterwards.

###Dependencies

This script runs on python3 and is written for the purpose of running as a cronjob.
To run it you'll only need  **python3**.

### Manual Usage

For testing purposes you can run the script from the shell. To do so, navigate to the project directory and run 

    python3 run_autoresponder.py

### Usage as a cronjob

For production use you can configure it as a cronjob.

From the shell, run:

	crontab -e

Then append to the file (replace "/the/path/to/the/project/folder" by the actual path to these files):

	*/1 * * * * python3 /the/path/to/the/project/folder/run_autoresponder.py

This will run the script every minute.

You can use any [Online](https://crontab-generator.org/) 
[Cron](https://www.freeformatter.com/cron-expression-generator-quartz.html) 
[Expression](http://www.cronmaker.com/) 
[Generator](http://cron.nmonitoring.com/cron-generator.html) for generating other cron expressions.

For info on how to craft the cron expression yourself, run `man crontab`.

