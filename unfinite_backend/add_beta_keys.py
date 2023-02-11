import sqlite3, csv, secrets

emails = []

filename = input('Name of csv file containing emails (including extension):\n-> ')
with open(filename, newline='\n') as csvfile:
    reader = csv.reader(csvfile)
    emails = list(map(lambda x: x[0], reader))
    csvfile.close()

keys = [secrets.token_urlsafe(32) for i in range(len(emails))]

con = sqlite3.connect('db.sqlite3')
cur = con.cursor()

for email, key in zip(emails, keys):

    cur.execute(f"INSERT INTO api_betakey (user_email, key) VALUES ('{email}', '{key}');")

out_filename = input('Name of csv file to dump emails and keys into (including extension):\n-> ')
with open(out_filename, 'w') as outfile:
    outfile.write('email, registration_key\n')
    for email, key in zip(emails, keys):
        outfile.write(f"{email}, {key}\n")
    outfile.close()
cur.close()
con.commit()
con.close()