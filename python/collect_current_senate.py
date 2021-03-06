def get_bio_text(df):
    import re
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd

    ## Loop thorugh every senator to get bios
    for i in range(len(df)):
        ## Go to url of each senator
        url = 'http://bioguide.congress.gov/scripts/biodisplay.pl?index={}'.format(df.loc[i, 'bioguide_id'])
        r = requests.get(url)
        c = r.content
        soup = BeautifulSoup(c, "lxml")

        ## Save bio text in data set
        bio_text = str(soup.findAll('p')[0])
        df.loc[i, 'bio_text'] = re.sub("<[^>]*>","",bio_text).replace('\r','').replace('\n','')
    return df

def get_bio_image(df):
    import requests
    from PIL import Image
    from StringIO import StringIO
    
    df.loc[:, 'image'] = None
    for i in range(len(df)):
        url = 'http://bioguide.congress.gov/bioguide/photo/{}/{}.jpg'.format(df['bioguide_id'][i][0], 
                                                                             df['bioguide_id'][i])
        r = requests.get(url)
        r.content
        try:
            image_save = Image.open(StringIO(r.content))
            image_save.save('../static/img/bio_images/{}.png'.format(df['bioguide_id'][i]))
            df.loc[i, 'image'] = True
        except:
            df.loc[i, 'image'] = False
    return df

def put_into_sql(data_set):
    import os
    import psycopg2
    import urlparse
    import pandas as pd

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
        cursor.execute("""DROP TABLE current_senate_bio;""")
    except:
        'table did not exist'

    sql_command = """
    CREATE TABLE current_senate_bio (
    address TEXT, 
    bioguide_id varchar(255) PRIMARY KEY, 
    class_ varchar(255), 
    email varchar(255), 
    first_name varchar(255), 
    last_name varchar(255), 
    leadership_position varchar(255), 
    member_full varchar(255), 
    party varchar(255), 
    phone varchar(255), 
    state varchar(255), 
    website varchar(255),
    bio_text TEXT,
    photo_url varchar(255));"""


    cursor.execute(sql_command)
    for i in range(len(data_set)):
        print i
        data_set.loc[i, 'bio_text'] = data_set.loc[i, 'bio_text'].replace("'", "''")
        data_set.loc[i, 'bio_text'] = str(data_set.loc[i, 'bio_text'].decode('unicode_escape').encode('ascii','ignore'))
        x = list(data_set.loc[i,])
        
        
        
        for p in [x]:
            format_str = """INSERT INTO current_senate_bio (
            address, 
            bioguide_id, 
            class_, 
            email, 
            first_name, 
            last_name,
            leadership_position, 
            member_full, 
            party, 
            phone, 
            state, 
            website,
            bio_text,
            photo_url)
            VALUES ('{address}', '{bioguide_id}', '{class_}', '{email}', '{first_name}', '{last_name}', 
            '{leadership_position}', '{member_full}', '{party}', '{phone}', '{state}',
            '{website}', '{bio_text}', '{photo_url}');"""

            sql_command = format_str.format(address=p[0], bioguide_id=p[1], class_=p[2], email=p[3], first_name=p[4], last_name=p[5], 
                              leadership_position=p[6], member_full=p[7], party=p[8],phone=p[9], state=p[10],
                              website=p[11], bio_text=p[12], photo_url=p[13])
            cursor.execute(sql_command)

    # never forget this, if you want the changes to be saved:
    connection.commit()
    connection.close()

def get_senate_by_gov():
    import pandas as pd
    import requests
    from json import dumps
    from xmljson import badgerfish as bf
    import xmltodict
    from xml.etree import ElementTree
    from pandas.io.json import json_normalize
    import urllib
    
    """Some of the urls don't work the first time,
    but by setting a proxy requests sends info to 
    senate.gov to connect to the page"""
    s = requests.Session()
    s.auth = ('user', 'pass')
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    url = 'http://www.senate.gov/general/contact_information/senators_cfm.xml'
    print url
    
    r =  requests.post(url, headers=headers)
    print r.status_code

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
        r = requests.post(url, data=dumps(payload), headers=headers)
    if r.status_code == 403:
        df = pd.DataFrame()
        return df, 403

    x = ElementTree.fromstring(r.content)
    x = bf.data(x)
    x = pd.DataFrame(x).loc['member', 'contact_information']
    df = json_normalize(x)
    df.columns = df.columns.str.replace('$', '').str.replace('.', '')

    return df, 200

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

    cursor = connection.cursor()

    df_checker = pd.read_sql_query("""select * from current_senate_bio""", connection)
    connection.close()
    
    df.loc[:,'duplicate'] = df.loc[:,'bioguide_id'].apply(lambda x: len(df_checker.loc[df_checker['bioguide_id'].astype(str) == str(x)]) > 0)
    if len(df.loc[df['duplicate']==False]) > 0:
        return True
    elif len(df.loc[df['duplicate']==False]) == 0:
        return False


def get_senator_info():    
    import pandas as pd
    import time


    ## pass data through data collection functions
    print 'data collection 1'
    df, status_code_int = get_senate_by_gov()

    if status_code_int == 403:
        scraper_counter = 0
        while status_code_int == 403: 
            if scraper_counter < 10:
                time.sleep(5)
                df, status_code_int = get_senate_by_gov()
            elif scraper_counter == 10:
                return "But it got a status code of 403 Forbidden HTTP"
            scraper_counter += 1
    ## It only makes it here if it collected data.
    ## If 403 too many times the function returns
    keep_moving = create_new_table_checker(df)
    keep_moving = True
    print 'should I keep scraping? {}'.format(keep_moving)
    if keep_moving == True:
        print 'data collection 2'
        df = get_bio_text(df)
        df['photo_url'] = df['bioguide_id'].apply(lambda x: 'http://bioguide.congress.gov/bioguide/photo/{}/{}.jpg'.format(x[0],x))
        print 'put into sql'
        put_into_sql(df)
        print 'done!'
        return 'Data was collected'
    elif keep_moving == False:
        return 'No New Data was collected'