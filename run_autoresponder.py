#!/usr/bin/python
import configparser
import email
import email.header
import email.mime.text
import imaplib
import re
import smtplib
import sys

config = None
incoming_mail_server = None
outgoing_mail_server = None
processed_mail_counter = 0
pattern_uid = re.compile('\d+ \(UID (?P<uid>\d+)\)')


def run():
    print("--- Python Reply-To Autoresponder ---")
    initialize()
    connect_to_mail_servers()
    mails = fetch_emails()
    for mail in mails:
        process_email(mail)
    print("Closing connection...")
    incoming_mail_server.close()
    incoming_mail_server.logout()
    outgoing_mail_server.quit()
    print("Script run successful.")


def initialize():
    if "--help" in sys.argv or "-h" in sys.argv:
        display_help_text()
    config_file_location = "autoresponder.config.ini"
    if "--config-path" in sys.argv and len(sys.argv) >= 3:
        config_file_location = sys.argv[2]
    print("Using '" + config_file_location + "' as location for config file.")
    load_config_from_file(config_file_location)


def display_help_text():
    print("Options:")
    print("\t--help: Display this help information")
    print("\t--config-path <path/to/config/file>: "
          "Override path to config file (defaults to same directory as the script is)")
    exit(1)


def load_config_from_file(file_path):
    config_file = configparser.ConfigParser()
    config_file.read(file_path, encoding="ISO-8859-1")
    global config
    config = {
        'in.user': str(config_file["login credentials"]["mailserver.incoming.username"]),
        'in.pw': str(config_file["login credentials"]["mailserver.incoming.password"]),
        'out.user': str(config_file["login credentials"]["mailserver.outgoing.username"]),
        'out.pw': str(config_file["login credentials"]["mailserver.outgoing.password"]),
        'display.name': str(config_file["login credentials"]["mailserver.outgoing.display.name"]),
        'display.mail': str(config_file["login credentials"]["mailserver.outgoing.display.mail"]),
        'in.host': str(config_file["mail server settings"]["mailserver.incoming.imap.host"]),
        'in.port': str(config_file["mail server settings"]["mailserver.incoming.imap.port.ssl"]),
        'out.host': str(config_file["mail server settings"]["mailserver.outgoing.smtp.host"]),
        'out.port': str(config_file["mail server settings"]["mailserver.outgoing.smtp.port.tls"]),
        'folders.inbox': str(config_file["mail server settings"]["mailserver.folders.inbox.name"]),
        'folders.trash': str(config_file["mail server settings"]["mailserver.folders.trash.name"]),
        'request.from': str(config_file["mail content settings"]["mail.request.from"]),
        'reply.subject': str(config_file["mail content settings"]["mail.reply.subject"].strip()),
        'reply.body': str(config_file["mail content settings"]["mail.reply.body"].strip())
    }


def connect_to_mail_servers():
    connect_to_imap()
    connect_to_smtp()


def connect_to_imap():
    print("Connecting to IMAP server '" + config['in.host']
          + "' on port " + config['in.port'] + " as user '" + config['in.user'] + "'.")

    global incoming_mail_server
    incoming_mail_server = imaplib.IMAP4_SSL(config['in.host'], config['in.port'])

    try:
        (retcode, capabilities) = incoming_mail_server.login(config['in.user'], config['in.pw'])
        if retcode != "OK":
            print_error_and_exit("Login failed with return code '" + retcode + "'!")
        print("IMAP login successful!")
    except Exception as e:
        print_error_and_exit(e)


def print_error_and_exit(error):
    print("Unexpected error occurred!")
    print(str(error))
    global incoming_mail_server
    if incoming_mail_server is not None:
        try:
            incoming_mail_server.close()
            incoming_mail_server.logout()
        except Exception:
            pass
    if outgoing_mail_server is not None:
        try:
            outgoing_mail_server.quit()
        except Exception:
            pass
    exit(-1)


def connect_to_smtp():
    print("Connecting to SMTP server '" + config['out.host']
          + "' on port " + config['out.port'] + " as user '" + config['out.user'] + "'.")

    global outgoing_mail_server
    outgoing_mail_server = smtplib.SMTP(config['out.host'], config['out.port'])
    outgoing_mail_server.starttls()

    try:
        (retcode, capabilities) = outgoing_mail_server.login(config['out.user'], config['out.pw'])
        if retcode != 235:
            print_error_and_exit("Login failed with return code '" + str(retcode) + "'!")
        print("SMTP login successful!")
    except Exception as e:
        print_error_and_exit(e)


def fetch_emails():
    # get the message ids from the inbox folder
    incoming_mail_server.select(config['folders.inbox'])
    (retcode, message_ids) = incoming_mail_server.search(None, 'ALL')
    if retcode == 'OK':
        messages = []
        for message_id in message_ids[0].split():
            # get the actual message for the id
            (retcode, data) = incoming_mail_server.fetch(message_id, '(RFC822)')
            if retcode != 'OK':
                print_error_and_exit("ERROR getting message with id '" + message_id + "'.")
            else:
                # parse the message into a useful format
                message = email.message_from_string(data[0][1].decode('utf-8'))
                message['autoresponder_email_id'] = message_id
                messages.append(message)
        print("Got " + str(len(messages)) + " emails from inbox.")
        return messages
    else:
        print("Inbox contains no emails.")
        return []


def process_email(mail):
    mail_sender = email.header.decode_header(mail['From'])[1]
    mail_sender = str(mail_sender[0], 'UTF-8')
    if config['request.from'] in mail_sender:
        reply_to_email(mail)
        delete_email(mail)
        global processed_mail_counter
        processed_mail_counter += 1
        print("Replied to and deleted " + str(processed_mail_counter) + " emails in total.")
    else:
        # TODO handle mails from incorrect senders
        pass


def reply_to_email(mail):
    receiver_email = email.header.decode_header(mail['Reply-To'])[0][0]
    message = email.mime.text.MIMEText(config['reply.body'])
    message['Subject'] = config['reply.subject']
    message['To'] = receiver_email
    message['From'] = email.utils.formataddr((
        str(email.header.Header(config['display.name'], 'utf-8')), config['display.mail']))
    outgoing_mail_server.sendmail(config['display.mail'], receiver_email, message.as_string())


def delete_email(mail):
    (resp, data) = incoming_mail_server.fetch(mail['autoresponder_email_id'], "(UID)")
    mail_uid = parse_uid(str(data[0], 'UTF-8'))
    result = incoming_mail_server.uid('COPY', mail_uid, config['folders.trash'])
    if result[0] != "OK":
        print("Copying mail to trash failed. Deleting anyways to prevent multiple response mails. "
              "Reason for failure: " + str(result))
    incoming_mail_server.uid('STORE', mail_uid, '+FLAGS', '(\Deleted)')
    incoming_mail_server.expunge()


def parse_uid(data):
    match = pattern_uid.match(data)
    return match.group('uid')


run()
