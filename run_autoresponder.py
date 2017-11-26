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
    global config
    config = configparser.ConfigParser()
    config.read(file_path, encoding="ISO-8859-1")


def connect_to_mail_servers():
    connect_to_imap()
    connect_to_smtp()


def connect_to_imap():
    host = str(config["mail server settings"]["mailserver.incoming.imap.host"])
    port = str(config["mail server settings"]["mailserver.incoming.imap.port.ssl"])
    user = str(config["login credentials"]["mailserver.incoming.username"])
    password = str(config["login credentials"]["mailserver.incoming.password"])
    print("Connecting to IMAP server '" + host
          + "' on port " + port + " as user '" + user + "'.")

    global incoming_mail_server
    incoming_mail_server = imaplib.IMAP4_SSL(host, port)

    try:
        (retcode, capabilities) = incoming_mail_server.login(user, password)
        if retcode != "OK":
            print_error_and_exit("Login failed with return code '" + retcode + "'!")
        print("Login success!")
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
    host = str(config["mail server settings"]["mailserver.outgoing.smtp.host"])
    port = str(config["mail server settings"]["mailserver.outgoing.smtp.port.tls"])
    user = str(config["login credentials"]["mailserver.outgoing.username"])
    password = str(config["login credentials"]["mailserver.outgoing.password"])
    print("Connecting to SMTP server '" + host
          + "' on port " + port + " as user '" + user + "'.")

    global outgoing_mail_server
    outgoing_mail_server = smtplib.SMTP(host, port)
    outgoing_mail_server.starttls()

    try:
        (retcode, capabilities) = outgoing_mail_server.login(user, password)
        if retcode != 235:
            print_error_and_exit("Login failed with return code '" + str(retcode) + "'!")
        print("Login success!")
    except Exception as e:
        print_error_and_exit(e)


def fetch_emails():
    inbox = str(config["mail server settings"]["mailserver.folders.inbox.name"])
    # get the message ids from the inbox folder
    incoming_mail_server.select(inbox)
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
    expected_mail_sender = str(config["mail content settings"]["mail.request.from"])
    mail_sender = email.header.decode_header(mail['From'])[1]
    mail_sender = str(mail_sender[0], 'UTF-8')
    if expected_mail_sender in mail_sender:
        reply_to_email(mail)
        delete_email(mail)
        global processed_mail_counter
        processed_mail_counter += 1
        print("Replied to and deleted " + str(processed_mail_counter) + " emails.")
    else:
        # TODO handle mails from incorrect senders
        pass


def reply_to_email(mail):
    reply_mail_subject = str(config["mail content settings"]["mail.reply.subject"]).strip()
    reply_mail_body = str(config["mail content settings"]["mail.reply.body"]).strip()
    reply_to = email.header.decode_header(mail['Reply-To'])[0][0]
    send_email(reply_to, reply_mail_subject, reply_mail_body)


def send_email(receiver_email, email_subject, email_body):
    sender_name = str(config["login credentials"]["mailserver.outgoing.display.name"])
    sender_email = str(config["login credentials"]["mailserver.outgoing.display.mail"])
    message = email.mime.text.MIMEText(email_body)
    message['Subject'] = email_subject
    message['To'] = receiver_email
    message['From'] = email.utils.formataddr((str(email.header.Header(sender_name, 'utf-8')), sender_email))
    outgoing_mail_server.sendmail(sender_email, receiver_email, message.as_string())


def delete_email(mail):
    trash = str(config["mail server settings"]["mailserver.folders.trash.name"])
    mail_index = mail['autoresponder_email_id']
    (resp, data) = incoming_mail_server.fetch(mail_index, "(UID)")
    mail_uid = parse_uid(str(data[0], 'UTF-8'))
    result = incoming_mail_server.uid('COPY', mail_uid, trash)
    if result[0] != "OK":
        print("Copying mail to trash failed. Deleting anyways to prevent multiple response mails. "
              "Reason for failure: " + str(result))
    incoming_mail_server.store(mail_index, '+FLAGS', '\Deleted')
    incoming_mail_server.expunge()


def parse_uid(data):
    match = pattern_uid.match(data)
    return match.group('uid')


run()
