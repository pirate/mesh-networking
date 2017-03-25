import sqlite3

from shell_tools import run_cmd

def get_skype_info(main_user):
    try:
        db_path = find_profiles(main_user)
        yield '[>]      Skype:'
        for line in get_profile_info(db_path):
            yield '[>]         %s' % line
    except Exception:
        yield '[>]      Skype:     None Found.'

def find_profiles(user=None):
    if user and user != "root":
        paths = run_cmd("find /Users/%s/Library/Application\ Support/Skype -name 'main.db'" % user)
    else:
        paths = run_cmd("find /*/*/Users/*/Library/Application\ Support/Skype -name 'main.db'")
        root_skypes = run_cmd("find /var/root/Library/Application\ Support/Skype -name 'main.db'")
        paths.extend([path for path in root_skypes if path])
    return paths

def get_profile_info(skype_dbs):
    for DB in skype_dbs:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT fullname, skypename, city, country, datetime(profile_timestamp,'unixepoch') FROM Accounts;")
        for row in c:
            yield '[*] -- %s --' % str(row[1])
            yield '[+] Name: ' + str(row[0])
            yield '[+] Location: ' + str(row[2]) + ',' + str(row[3])
            yield '[+] Profile Date: ' + str(row[4])

def get_contacts(skype_dbs):
    for DB in skype_dbs:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT displayname, skypename, city, country, phone_mobile, birthday FROM Contacts;")
        for row in c:
            name, username = row[0], row[1]
            location = row[2], row[3]
            mobile, birthday = row[4], row[5]

            yield '\n[*] -- %s --' % row[1]
            yield '[+] Name                : %s' % row[0]
            if location[0] or location[1]:
                yield '[+] Location            : %s,%s' % location
            if mobile:
                yield '[+] Mobile Number       : %s' % mobile
            if birthday:
                yield '[+] Birthday            : %s' % birthday

def get_calls(skype_dbs):
    for DB in skype_dbs:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM calls, conversations;")

        yield '\n[*] -- Found Calls --'
        for row in c:
            yield '[+] %s (%ss)' % (row[1], row[0])

def get_messages(skype_dbs):
    for DB in skype_dbs:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT datetime(timestamp,'unixepoch'), dialog_partner, author, body_xml FROM Messages;")
        messages = [];
        for row in c:
            try:
                if row[2] == row[1]:
                    tofrom = '[%s] From[%s] To[%s]: ' % (row[0], row[2], 'user')
                else:
                    tofrom = '[%s] From[%s] To[%s]: ' % (row[0], 'user', row[1])
                messages.append(tofrom.ljust(70)+row[3])
            except:
                pass
    return messages

def purge_messages(skype_dbs, conversation_partner):
    for DB in skype_dbs:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT datetime(timestamp,'unixepoch'), dialog_partner, author, body_xml FROM Messages WHERE dialog_partner = '%s'" % conversation_partner)
        c.execute("DELETE FROM messages WHERE skypename = '%s'" % conversation_partner)
