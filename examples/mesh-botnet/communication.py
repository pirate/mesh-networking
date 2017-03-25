import os
from shell_tools import run_cmd
from settings import HOSTNAME, MAIN_USER

default_from = '%s@%s' % (MAIN_USER, HOSTNAME)

help_str = """
    sudo mkdir -p /Library/Server/Mail/Data/spool
    sudo /usr/sbin/postfix set-permissions
    sudo /usr/sbin/postfix start
"""

def email(to='medusa@sweeting.me', _from=default_from, subject='BOT MSG', message="Info email", attachments=None):
    """function to send mail to a specified address with the given attachments"""
    for attachment in attachments or []:
        filename = attachment.strip()
        try:
            result = run_cmd('uuencode %s %s | mailx -s "%s" %s' % (filename, filename, subject, to))[0]
            return "Sending email From: %s; To: %s; Subject: %s; Attachment: %s (%s)" % (_from, to, subject, filename, result or 'Succeded')
        except Exception as error:
            return str(error)

    if not attachments:
        p = os.popen("/usr/sbin/sendmail -t", "w")
        p.write("From: %s\n" % _from)
        p.write("To: %s\n" % to)
        p.write("Subject: %s\n" % subject)
        p.write("\n")   # blank line separating headers from body
        p.write('%s\n' % message)
        result = p.close()

    if not result:
        return "Sent email From: %s; To: %s; Subject: %s; Attachments: %s)" % (_from, to, subject, ','.join(attachments or []))
    else:
        return "Error: %s. Please fix Postfix:\n %s" % (result, help_str)
