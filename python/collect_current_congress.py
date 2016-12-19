import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

def get_congress_by_gov():
    df = pd.DataFrame()
    url = 'https://congress.gov/members?q=%7B%22chamber%22%3A%22House%22%2C%22congress%22%3A%22114%22%7D'
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    page = requests.get(url, headers=headers)
    if page.status_code == 403:
        payload = {
            "Host": "www.mywbsite.fr",
            "Connection": "keep-alive",
            "Content-Length": 129,
            "Origin": "https://www.mywbsite.fr",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Referer": "https://www.mywbsite.fr/data/mult.aspx",
            "Accept-Encoding": "gzip,deflate,sdch",
            "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Cookie": "ASP.NET_SessionId=j1r1b2a2v2w245; GSFV=FirstVisit=; GSRef=https://www.google.fr/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&ved=0CHgQFjAA&url=https://www.mywbsite.fr/&ei=FZq_T4abNcak0QWZ0vnWCg&usg=AFQjCNHq90dwj5RiEfr1Pw; HelpRotatorCookie=HelpLayerWasSeen=0; NSC_GSPOUGS!TTM=ffffffff09f4f58455e445a4a423660; GS=Site=frfr; __utma=1.219229010.1337956889.1337956889.1337958824.2; __utmb=1.1.10.1337958824; __utmc=1; __utmz=1.1337956889.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)"
        }
        # Adding empty header as parameters are being sent in payload
        headers = {}
        page = requests.post(url, data=dumps(payload), headers=headers)
    if page.status_code == 403:
        return df, 403
    c = page.content
    soup = BeautifulSoup(c, "lxml")

    loop_range = int(str(soup.find_all(
            'span', id='facetItemcongress114__2015_2016_count')
                    ).split('">[')[1].split(']<')[0])

    for i in range(0,loop_range):
        page_search = i + 1
        url = 'https://congress.gov/members?q=%7B%22chamber%22%3A%22House%22%2C%22congress%22%3A%22114%22%7D&pageSize=1&page={}'.format(page_search)
        page = requests.get(url, headers=headers)
        c = page.content
        soup = BeautifulSoup(c, "lxml")
        soup.find_all('span', class_="result-heading")

        try:
            df.loc[i, 'name'] = str(soup.find_all('span', class_="result-heading"
                                                 )[0]).split('https://www.congress.gov/member/'
                                                            )[1].split('/')[0].replace('-',' ')
        except:
            df.loc[i, 'name'] = None

        try:
            df.loc[i, 'bioguide_id'] = str(soup.find_all('span', class_="result-heading"
                                                        )[0]).split('<a href="')[1].split('">')[0].split('/')[-1]
        except: 
            df.loc[i, 'bioguide_id'] = None

        try:
            df.loc[i, 'state'] = str(soup.find_all('div', class_="quick-search-member"
                                                  )[0]).split('State:')[1].split(
                '<span>')[1].split('</span>')[0]
        except:
            df.loc[i, 'state'] = None
## This needs to switch to int

        try:
            df.loc[i, 'district'] = str(soup.find_all('div', class_="quick-search-member"
                                                     )[0]).split('District:')[1].split(
                '<span>')[1].split('</span>')[0]
        except:
            df.loc[i, 'district'] = 'at large'

        try:
            df.loc[i, 'party'] = str(soup.find_all('div', class_="quick-search-member"
                                                  )[0]).split('Party:')[1].split(
                '<span>')[1].split('</span>')[0]
        except:
            df.loc[i, 'party'] = None

        try:
            df.loc[i, 'year_elected'] = str(soup.find_all('div', class_="quick-search-member"
                                                         )[0]).split('House: ')[1].split(
                '</li>')[0].split('-')[0]
        except:
            df.loc[i, 'year_elected'] = None

    return df, 200

def get_bio_image(df):
    from PIL import Image
    from StringIO import StringIO
    
    df.loc[:, 'image'] = None
    for i in range(len(df)):
        try:
            url = 'http://bioguide.congress.gov/bioguide/photo/{}/{}.jpg'.format(df['bioguide_id'][i][0], 
                                                                                 df['bioguide_id'][i])
            r = requests.get(url)
            r.content
            image_save = Image.open(StringIO(r.content))
            image_save.save('../static/img/bio_images/{}.png'.format(df['bioguide_id'][i]))
            df.loc[i, 'image'] = True
        except:
            df.loc[i, 'image'] = False
    return df
    
def get_bio_text(df):
    import re

    ## Loop thorugh every senator to get bios
    for i in range(len(df)):
        ## Go to url of each senator
        url = 'http://bioguide.congress.gov/scripts/biodisplay.pl?index={}'.format(df.loc[i, 'bioguide_id'])
        r = requests.get(url)
        c = r.content
        soup = BeautifulSoup(c, "lxml")

        ## Save bio text in data set
        try:
            bio_text = str(soup.findAll('p')[0])
        except:
            bio_text = ''
        ## Remove html tags
        df.loc[i, 'bio_text'] = re.sub("<[^>]*>","",bio_text).replace('\r','').replace('\n','')
    return df

def collect_remaining_data(df):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }

    for i in range(len(df)):

        url = 'https://www.congress.gov/member/{}'.format(df.loc[i, 'bioguide_id'])
        page = requests.get(url, headers=headers)
        c = page.content
        soup = BeautifulSoup(c, "lxml")

        try:
            df.loc[i, 'leadership_position'] = str(soup.find_all('div', 
                                                                 class_="member_profile")
                                                  ).split('<h4>')[1].split('</h4>')[0]
        except:
            df.loc[i, 'leadership_position'] = None

        try:
            df.loc[i, 'website'] = str(soup.find_all('table', 
                                                     class_="standard01 nomargin")).split(
                '<a href="')[1].split('" ')[0]
        except:
            df.loc[i, 'website'] = None

        try:
            df.loc[i, 'address'] = str(soup.find_all('table',
                                                     class_="standard01 nomargin")).split(
                'Contact')[1].split('<br/>')[0].split('  ')[-1]
        except:
            df.loc[i, 'address'] = None

        try:
            df.loc[i, 'phone'] = str(soup.find_all('table', 
                                                   class_="standard01 nomargin")).split(
                'Contact')[1].split('<br/>')[1].split('  ')[0]
        except:
            df.loc[i, 'phone'] = None
    ## This is a placeholder until I can find these
    df.loc[:, 'email'] = None
    return df


def put_into_sql(df):
    import os
    import psycopg2
    import urlparse

    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_BROWN_URL"])

    connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
            )

    cursor = connection.cursor()

    ## delete 
    # I'm deleting to make sure we have the most
    # up-to-date reps. The collection is small
    # so it's not a bottle next to do this.
    try:
        cursor.execute("""DROP TABLE current_congress_bio;""")
    except:
        'table did not exist'


    # Create table
    sql_command = """
        CREATE TABLE current_congress_bio (
        name varchar(255), 
        bioguide_id varchar(255) PRIMARY KEY,  
        state varchar(255), 
        district varchar(255), 
        party varchar(255), 
        year_elected int, 
        bio_text TEXT,
        leadership_position varchar(255),
        website varchar(255),
        address varchar(255),
        phone varchar(255),
        email varchar(255));"""
    cursor.execute(sql_command)

    ## Put data into table
    for i in range(len(df)):
        print i
        df.loc[i, 'bio_text'] = df.loc[i, 'bio_text'].replace("'", "''")
        df.loc[i, 'bio_text'] = str(df.loc[i, 'bio_text'].decode('unicode_escape').encode('ascii','ignore'))
        x = list(df.loc[i,])

        for p in [x]:
            format_str = """INSERT INTO current_congress_bio (
            name, 
            bioguide_id,  
            state, 
            district, 
            party, 
            year_elected, 
            bio_text,
            leadership_position,
            website,
            address,
            phone,
            email)
            VALUES ('{name}', '{bioguide_id}', '{state}', '{district}', '{party}', '{year_elected}', 
            '{bio_text}', '{leadership_position}', '{website}', '{address}', '{phone}',
            '{email}');"""

            sql_command = format_str.format(name=p[0], bioguide_id=p[1], state=p[2], district=p[3], 
                                            party=p[4], year_elected=p[5], bio_text=p[6], 
                                            leadership_position=p[7], website=p[8],
                                            address=p[9], phone=p[10], email=p[11])
            cursor.execute(sql_command)
    # never forget this, if you want the changes to be saved:
    connection.commit()
    connection.close()

## Should I do more data collection?
def create_new_table_checker(df):
    import os
    import psycopg2
    import urlparse

    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_BROWN_URL"])

    connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
            )
    
    df_checker = pd.read_sql_query("""select * from current_congress_bio""", connection)
    connection.close()
    
    df.loc[:,'duplicate'] = df.loc[:,'bioguide_id'].apply(lambda x: len(df_checker.loc[df_checker['bioguide_id'] == x]) > 0)
    if len(df.loc[df['duplicate']==False]) == 0:
        return False
    elif len(df.loc[df['duplicate']==False]) > 0:
        return True

def collect_current_congress_house():
    """This script will collect data on current
    congression people, create a table in the database,
    and store them in said table"""
    
    
    df = pd.DataFrame()
    
    print 'getting data 1'
    df, status_code = get_congress_by_gov()
    print status_code
    print "length of df {}".format(len(df))
    if status_code == 403:
        return "But it got a status code of 403 Forbidden HTTP"
    else:
        print 'check if any of the reps collected are new reps'
        keep_moving = create_new_table_checker(df)
        print "should I keep moving {}".format(keep_moving)
        if keep_moving == True:

            print 'getting data 2'
            get_bio_text(df)
            print 'getting data 3'
            collect_remaining_data(df)

            # print 'get images'
            # get_bio_image(df)

            print 'put data in db'
            put_into_sql(df)
            
            print 'done!'
            return 'Data was collected'
        elif keep_moving == False:
            return 'No Data was collected'
