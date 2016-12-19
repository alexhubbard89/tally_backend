import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imp
collect_current_congress = imp.load_source('module', './python/collect_current_congress.py')
collect_current_senate = imp.load_source('module', './python/collect_current_senate.py')

fromaddr = 'tallyscraper@gmail.com'
toaddrs = 'alexhubbard89@gmail.com'

msg = MIMEMultipart('alternative')
msg['From'] = "tallyscraper@gmail.com"
msg['To'] = "alexhubbard89@gmail.com"
good_collection = ''
bad_collection = ''
try:
    to_collect_or_not_collect = collect_current_congress.collect_current_congress_house()
    good_collection += """
    Current Congress: {}""".format(to_collect_or_not_collect)
except:
    bad_collection += """
    Current Congress"""

try:
    to_collect_or_not_collect = collect_current_senate.get_senator_info()
    good_collection += """
    Current Senate: {}""".format(to_collect_or_not_collect)
except:
    bad_collection += """
    Current Senate"""

msg['Subject'] = "Data Collection Report"
body_msg = """Data Collection Report

Data colltion script(s) that worked: 
{}

Data colltion script(s) that didn't work: 
{}""".format(good_collection, bad_collection)
body = MIMEText(body_msg)
msg.attach(body)


username = 'tallyscraper@gmail.com'
password = os.environ["tallyscraper_password"]
server = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg.as_string())
server.quit()