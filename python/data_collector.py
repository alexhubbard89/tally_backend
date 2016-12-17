import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imp
collect_current_congress = imp.load_source('module', './python/collect_current_congress.py')

fromaddr = 'tallyscraper@gmail.com'
toaddrs = 'alexhubbard89@gmail.com'

msg = MIMEMultipart('alternative')
msg['From'] = "tallyscraper@gmail.com"
msg['To'] = "alexhubbard89@gmail.com"
# try:
collect_current_congress.collect_current_congress_house()
msg['Subject'] = "All good!"
body = MIMEText("You successfully scrapped data!")
msg.attach(body)
# except:
#     msg['Subject'] = "Something broke"
#     body = MIMEText("""Something about the data scraper went bad :(
#         collect_current_congress didn't work""")
#     msg.attach(body)

username = 'tallyscraper@gmail.com'
password = os.environ["tallyscraper_password"]
server = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg.as_string())
server.quit()