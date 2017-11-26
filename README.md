# Python Reply-To Autoresponder

Simple python script that connects to a mail server via IMAP and SMTP and replies to 
all emails in the inbox coming from a certain sender address using the Reply-To header.
Mails that have been replied to are deleted afterwards.

### Dependencies

This script runs on python3 and is written for the purpose of running as a cronjob.
To run it you'll only need  **python3**.

### Installation

To install, simply download a copy of the project (see screenshot below) and extract it to whatever folder you like.

![Github Archive Download](https://user-images.githubusercontent.com/6501308/33236233-4de2d6fe-d24d-11e7-9581-9a59d9615c12.PNG)

### Configuration 

Before first run, you need to adapt the project to your needs by editing the `autoresponder.config.ini` file with a text editor.

The required configuration items for the individual sections are listed below.

**Section [login credentials]**

| Configuration Item | Description |
| ------------------ | ----------- |
| mailserver.incoming.username     | The username to use for logging in at the IMAP server hosting the inbox, usually an email address. |
| mailserver.incoming.password     | The password to use for logging in at the IMAP server hosting the inbox. |
| mailserver.outgoing.username     | The username to use for logging in at the SMTP server for sending the reply, usually an email address. |
| mailserver.outgoing.password     | The password to use for logging in at the SMTP server for sending the reply. |
| mailserver.outgoing.display.name | The name to use in the email's "From" field indicating where the reply email is from. |
| mailserver.outgoing.display.mail | The email address to use in the email's "From" field, should normally be a no-reply address. |

**Section [mail server settings]**

| Configuration Item | Description  |
| ------------------ | ------------ |
| mailserver.incoming.imap.host     | The hostname, domain or IP of the IMAP server hosting the inbox. |
| mailserver.incoming.imap.port.ssl | The port to use for SSL communication with the IMAP server. |
| mailserver.outgoing.smtp.host     | The hostname, domain or IP of the SMTP server for sending the reply. |
| mailserver.outgoing.smtp.port.tls | The port to use for TLS communication with the SMTP server. |
| mailserver.folders.inbox.name     | The name of the inbox folder, normally this is "Inbox". |

**Section [mail content settings]**

| Configuration Item | Description |
| ------------------ | ----------- |
| mail.request.from  | The sender email address to check new mails against. If an email is found in the inbox with this sender address, a reply is triggered. |
| mail.reply.subject | The subject line of the reply email. |
| mail.reply.body    | The plain text body of the reply email. |

After configuring the project, you can run it manually to test if your configuration works.

### Manual Usage

For testing purposes you can run the script from the shell. To do so, navigate to the project directory and run 

    python3 run_autoresponder.py

If you want to run the script multiple times with different configurations on each executions, 
you can achieve that by running

    python3 run_autoresponder.py --config-path /the/path/to/your/config/file/autoresponder.config.ini

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

### ToDos

* handle mails from incorrect senders
* check config for correctness during initialization
* test email folders during initialization
* implement proper error handling
* switch encoding of config.ini to non-Windows
* make use of reply-to field optional
