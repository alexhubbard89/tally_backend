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

def open_connection():
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
    return connection

def put_into_sql(data_set):
    import os
    import psycopg2
    import urlparse
    import pandas as pd

    connection = open_connection()
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
    address varchar(255), 
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
    bio_text TEXT;"""

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
            bio_text)
            VALUES ("{address}", "{bioguide_id}", "{class_}", "{email}", "{first_name}", "{last_name}", 
            "{leadership_position}", "{member_full}", "{party}", "{phone}", "{state}",
            "{website}", "{bio_text}");"""

            sql_command = format_str.format(address=p[0], bioguide_id=p[1], class_=p[2], email=p[3], first_name=p[4], last_name=p[5], 
                              leadership_position=p[6], member_full=p[7], party=p[8],phone=p[9], state=p[10],
                              website=p[11], bio_text=p[12])
            cursor.execute(sql_command)

    # never forget this, if you want the changes to be saved:
    connection.commit()
    connection.close()

def get_senate_by_gov(df):
    import pandas as pd
    import requests
    from json import dumps
    from xmljson import badgerfish as bf
    import xmltodict
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
    r =  requests.get(url, headers=headers, proxies=urllib.getproxies())

    x = xmltodict.parse(r.content)
    x = pd.DataFrame(x).loc['member', 'contact_information']
    df = json_normalize(x)
    df.columns = df.columns.str.replace('$', '').str.replace('.', '')

    return df


def get_senator_info():
    
    import pandas as pd

    ## make dataframe to pass through functions
    df = pd.DataFrame()

    ## pass data through data collection functions
    print 'data collection 1'
    df = get_senate_by_gov(df)
    print 'data collection 2'
    df = get_bio_text(df)
    print 'put into sql'
    put_into_sql(df)

    print 'done!'