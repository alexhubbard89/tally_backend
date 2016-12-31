import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

def most_recent_congress_number():
    ## Get current congress
    url = 'https://www.congress.gov/members'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    r = requests.get(url, headers=headers)
    page = BeautifulSoup(r.content, 'lxml')
    
    return int(str(page.find_all('ul', id='innerbox_congress')).split('facetItemcongress')[1].split('__')[0])


def get_congress_by_gov(congress_num):
    import pandas as pd
    import numpy as np
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime
    from json import dumps


    df = pd.DataFrame()

    for i in range(1,3):

        url = 'https://congress.gov/members?q=%7B"chamber":"House","congress":"{}"%7D&pageSize=250&page={}'.format(congress_num, i)
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 403:
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
            r = requests.get(url, data=dumps(payload), headers=headers)
            if r.status_code == 403:
                return df, 403
        
        page = BeautifulSoup(r.content, 'lxml')
        
        ## Just keep the data I need
        x = page.find_all('ol', class_='basic-search-results-lists expanded-view')
        split_data = str(x).split('<li class="expanded">')
        
        ## Extract only what I need. Helps performance
        for j in range(1, len(split_data)):
        ## Because the loop goes more than once I have to fix the index
            index_num = len(df)
            df.loc[index_num, 'name'] = split_data[j].split('https://www.congress.gov/member/')[1].split('/')[0].replace('-',' ')
            df.loc[index_num, 'bioguide_id'] = split_data[j].split('<a href="')[1].split('">')[0].split('/')[-1]
            df.loc[index_num, 'state'] = split_data[j].split('State:')[1].split('<span>')[1].split('</span>')[0]
            try: 
                df.loc[index_num, 'district'] = split_data[j].split('District:')[1].split('<span>')[1].split('</span>')[0]
            except:
                df.loc[index_num, 'district'] = 0
            df.loc[index_num, 'party'] = split_data[j].split('Party:')[1].split('<span>')[1].split('</span>')[0]
            df.loc[index_num, 'year_elected'] = split_data[j].split('member-served')[1].split('House: ')[1].split('-')[0]
            df.loc[index_num, 'served_until'] = split_data[j].split('member-served')[1].split('House: ')[1].split('-')[1].split('</li>')[0]
    return df.reset_index(drop=True), 200

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

    print 'total {}'.format(len(df))
    ## Loop thorugh every senator to get bios
    for i in range(len(df)):
        print i
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
    print 'total {}'.format(len(df))
    for i in range(len(df)):
        print i

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
        cursor.execute("""DROP TABLE congress_bio;""")
    except:
        'table did not exist'



    # Create table
    sql_command = """
        CREATE TABLE congress_bio (
        name varchar(255), 
        bioguide_id varchar(255) PRIMARY KEY,  
        state varchar(255), 
        district int, 
        party varchar(255), 
        year_elected int, 
        served_until varchar(255),
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
        print x

        for p in [x]:
            format_str = """INSERT INTO congress_bio (
            name, 
            bioguide_id,  
            state, 
            district, 
            party, 
            year_elected,
            served_until,
            bio_text,
            leadership_position,
            website,
            address,
            phone,
            email)
            VALUES ('{name}', '{bioguide_id}', '{state}', '{district}', '{party}', '{year_elected}', 
            '{served_until}','{bio_text}', '{leadership_position}', '{website}', '{address}', '{phone}',
            '{email}');"""

            sql_command = format_str.format(name=p[0], bioguide_id=p[1], state=p[2], district=p[3], 
                                            party=p[4], year_elected=p[5], served_until=p[6], bio_text=p[7], 
                                            leadership_position=p[8], website=p[9],
                                            address=p[10], phone=p[11], email=p[12])
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
    
    df_checker = pd.read_sql_query("""select * from congress_bio where served_until = 'Present'""", connection)
    connection.close()

    df = df.loc[df['served_until'] == 'Present'].reset_index(drop=True)
    df.loc[:,'duplicate'] = df.loc[:,'bioguide_id'].apply(lambda x: len(df_checker.loc[df_checker['bioguide_id'].astype(str) == str(x)]) > 0)
    if len(df.loc[df['duplicate']==False]) == 0:
        return False
    elif len(df.loc[df['duplicate']==False]) > 0:
        return True

def collect_current_congress_house():
    """This script will collect data on current
    congression people, create a table in the database,
    and store them in said table"""

    print 'get current congress number'
    current_congress = most_recent_congress_number()

    print 'getting data 1'
    df, status_code = get_congress_by_gov(current_congress)
    print status_code

    if status_code == 403:
        scraper_counter = 0
        while status_code == 403:
            if scraper_counter == 10:
                return "But it got a status code of 403 Forbidden HTTP" 
            elif scraper_counter < 10:
                df, status_code = get_congress_by_gov(current_congress)
    keep_moving = create_new_table_checker(df)
    print 'should I keep scraping? {}'.format(keep_moving)
    if keep_moving == False:
        print 'I have the most up to date data!'
        return 'No New Data was collected'
    elif keep_moving == True:
        ## Collect all data
        master_house_reps = pd.DataFrame()
        for i in range(101,current_congress+1):
            print i
            master_house_reps = master_house_reps.append(get_congress_by_gov(i))
        master_house_reps = master_house_reps.sort_values(['state', 'district']).drop_duplicates().reset_index(drop=True)
        print 'getting data 2'
        master_house_reps = get_bio_text(master_house_reps)
        print 'getting data 3'
        master_house_reps = collect_remaining_data(master_house_reps)

        print 'clean zee data'
        master_house_reps.loc[master_house_reps['leadership_position'].isnull(), 'leadership_position'] = None
        master_house_reps.loc[master_house_reps['website'].isnull(), 'website'] = None
        master_house_reps.loc[master_house_reps['address'].isnull(), 'address'] = None
        master_house_reps.loc[master_house_reps['phone'].isnull(), 'phone'] = None
        master_house_reps.loc[master_house_reps['email'].isnull(), 'email'] = None

        print 'put into sql'
        put_into_sql(master_house_reps)
        print 'donezo!'
        return 'All Data was collected!'