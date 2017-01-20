from __future__ import division
import pandas as pd
import itertools
import os
import json
import requests
import BeautifulSoup
from pandas.io.json import json_normalize
import psycopg2
import urlparse
import us
import math
from scipy import stats
from psycopg2 import IntegrityError
# from pyzipcode import ZipCodeDatabase
# zcdb = ZipCodeDatabase()
# import zipcode
from uszipcode import ZipcodeSearchEngine


try:
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_BROWN_URL"])

    connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    connection.close()
    def open_connection():
        connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
            )
        return connection
except:
    urlparse.uses_netloc.append("postgres")
    creds = pd.read_json('db_creds.json').loc[0,'creds']

    connection = psycopg2.connect(
        database=creds['database'],
        user=creds['user'],
        password=creds['password'],
        host=creds['host'],
        port=creds['port']
    )
    connection.close()
    def open_connection():
        connection = psycopg2.connect(
            database=creds['database'],
            user=creds['user'],
            password=creds['password'],
            host=creds['host'],
            port=creds['port']
            )
        return connection


def dict_gen(sql_query):
    """Turn sqlite3 query into dicitonary. This is Essential
    for returning json results. jsonify will not return sqlite3
    results because its a table, but it will return dic results."""
    connection = open_connection()
    cursor = connection.cursor()
    cursor.execute(sql_query)
    field_names = [d[0].lower() for d in cursor.description]
    while True:
        rows = cursor.fetchmany()
        if not rows: 
            connection.close()
            return
        for row in rows:
            yield dict(itertools.izip(field_names, row))



def get_state_by_zip(zip_code):
    """Find your senator by zipcode.  Because there are only 
    two senators and entire states are represented by those
    two senetors, I only need to find the state from the zip
    code and then locate the current senator. The input is the
    zip code, and the output is the state. The state will be
    pass into a sql query"""
    try:
        url = 'http://maps.googleapis.com/maps/api/geocode/json?address={}&sensor=true'.format(zip_code)
        r = requests.get(url)
        x = pd.DataFrame(json_normalize(r.json()['results']).loc[0, 'address_components']).loc[:,]
        for i in range(len(x['types'])):
            if u'administrative_area_level_1' in x.loc[i, 'types']:
        ## Save state from zipcode
                state = str(x.loc[i, 'short_name'].upper())

        return state
    except IndexError:
        "No data"
        return None


#def get_district_from_address(street, city, zip_code):
def get_district_from_address(street, city, state_short, state_long):
    import requests
    import us
    
    state = '{}{}'.format(state_short, state_long)
    
    s = requests.Session()
    s.auth = ('user', 'pass')
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    url = 'http://ziplook.house.gov/htbin/findrep?ADDRLK'
    form_data = {
        'street': street,
        'city': city,
        'state': state,
        'submit': 'FIND YOUR REP',
    }

    response = requests.request(method='POST', url=url, data=form_data, headers=headers)
    district = str(response.content.split('src="/zip/pictures/{}'.format(state_short.lower()))[1].split('_')[0])
    return int(district)
    

def get_district_num(zip_code,state_short):
    s = requests.Session()
    s.auth = ('user', 'pass')
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    url = 'http://ziplook.house.gov/htbin/findrep?ZIP={}&Submit=FIND+YOUR+REP+BY+ZIP'.format(zip_code)
    r = requests.get(url, headers=headers)

    page = BeautifulSoup(r.content, "html5lib")
    x = str(page.find_all('div', id="PossibleReps")).split(
        'src="/zip/pictures/{}'.format(state_short.lower()))

    ## Since multiple district could appear I need to query to be dynamic
    first_query = 0
    total_query = ''
    for district_num in range(1, len(x)):
        if first_query == 0:
            total_query += "district = '{}'".format(int(str(x[district_num].split('_')[0])))
        if first_query > 0:
            total_query += " or district = '{}'".format(int(str(x[district_num].split('_')[0])))
        first_query += 1
    if total_query == "district = '0'":
        total_query = total_query.replace('0', 'at large')
    return total_query

## Get query to get vote menu up to day of year
def get_vote_menu_query():
    month_query = datetime.datetime.now().month
    day_query = datetime.datetime.now().day
    current_year = datetime.datetime.now().year

    query_str = ''
    query_counter = 0
    congress_num = 101
    session_num = 1

    for i in range(1989, current_year+1):
        if query_counter == 0:
            query_str += """
            (congress = {}
            and session = {}
            and vote_date <= {})""".format(congress_num,session_num,
                                          str(datetime.datetime.strptime(
                    '{}-{}-{}'.format(day_query,month_query,i), 
                    '%d-%m-%Y')).split(' ')[0])
        elif query_counter > 0:
            query_str += """
            or (congress = {}
            and session = {}
            and vote_date <= '{}')""".format(congress_num,session_num,
                                          str(datetime.datetime.strptime(
                    '{}-{}-{}'.format(day_query,month_query,i), 
                    '%d-%m-%Y')).split(' ')[0])
        query_counter +=1
        session_num +=1
        if session_num > 2:
            session_num = 1
            congress_num +=1
    return str(query_str)

## Query for highlevel vote menu
# Probs remove this
def get_vote_menu(db):
    sql_command = """
    select * from vote_menu
    where ({})""".format(get_vote_menu_query())
    df = pd.read_sql_query(sql_command, db)
    df = df.groupby(['congress', 'session', 'department']).count()['vote_id'].reset_index(drop=False)
    df.columns = ['congress', 'session', 'department', 'num_votes']
    df = df.loc[((df['department'] == 'house') |
        (df['department'] == 'senate'))].reset_index(drop=True)
    ## Get avearge for each department
    house_avg = df.loc[df['department'] == 'house', 'num_votes'].mean()
    senate_avg = df.loc[df['department'] == 'senate', 'num_votes'].mean()
    ## Get comparision for each department
    df.loc[df['department'] == 'house','num_votes_compared_to_avg'] = df.loc[
        df['department'] == 'house', 'num_votes'].apply(lambda x: x - house_avg)
    df.loc[df['department'] == 'senate','num_votes_compared_to_avg'] = df.loc[
        df['department'] == 'senate', 'num_votes'].apply(lambda x: x - senate_avg)

    df = df.transpose().to_dict()
    return df

## Find senator from zip code
def get_senator(zip_code):
    state_short = get_state_by_zip(zip_code)
    senator_result = [r for r in dict_gen("""select * 
            from current_senate_bio
            where lower(state) = lower('{}');""".format(state_short))]
    return senator_result

## Find congress person from zip code
def get_congress_leader(street, city, zip_code):
    state_short = get_state_by_zip(zip_code)
    state_long = str(us.states.lookup(state_short))
    district = get_district_from_address(street, city, state_short, state_long)

    congress_result = [r for r in dict_gen("""select * 
            from current_congress_bio
            where state = '{}'
            and ({});""".format(state_long, district))]
    return congress_result

## Return you congress persons recent votes
def get_congress_persons_votes(street, city, zip_code):
    congress_result = get_congress_leader(street, city, zip_code)
    total_query = ''
    for i in range(len(congress_result)):
        if i == 0:
            total_query += "bioguide_id = '{}'".format(
                pd.DataFrame(congress_result).loc[i, 'bioguide_id'])
        elif i > 0:
            total_query += "or bioguide_id = '{}'".format(
                pd.DataFrame(congress_result).loc[i, 'bioguide_id'])

    congress_person_votes = [r for r in dict_gen("""
        select congress_subset.*, 
        congress_vote_menu.question, 
        congress_vote_menu.title_description
        from (select distinct * 
        from congressional_votes_tbl 
        where ({}) 
        order by roll desc 
        limit {}) as congress_subset
        left join congress_vote_menu
        on (congress_subset.roll_id = congress_vote_menu.roll_id);""".format(
            total_query, 5*len(congress_result)))]
    ## Chnage datetime format
    for i in range(len(congress_person_votes)):
        congress_person_votes[i]['date'] = pd.to_datetime(
            congress_person_votes[i]['date'])

    return congress_person_votes

## Return your senators recent votes
def get_senator_votes(zip_code):
    state_short = get_state_by_zip(zip_code)
    senator_result = get_senator(zip_code)

    senator_votes = [r for r in dict_gen("""
       select senate_subset.*,
        senate_vote_menu.title,
        senate_vote_menu.question
        from (select distinct * 
        from senator_votes_tbl
        where lower(state) = lower('{}')
        order by roll desc 
        limit {})
        as senate_subset
        left join senate_vote_menu
        on (senate_subset.roll_id = senate_vote_menu.vote_id);""".format(
                state_short, 5*len(senator_result)))]
    ## Change datetime format
    for i in range(len(senator_votes)):
        senator_votes[i]['date'] = pd.to_datetime(
            senator_votes[i]['date'])
        
    return senator_votes


## Get the number of days your congressperson missed
def get_congress_days_missed(street, city, zip_code):
    connection = open_connection()

    query = """
    select *
    from
    (select bioguide_id, 
    count(votes_missed) as num_days_missed
    from
    (select votes_missed_df.*, 
    total_votes.total_votes
    from (select date, bioguide_id, count(distinct(roll_id)) as votes_missed
    from congressional_votes_tbl
    where lower(vote) = 'not voting'
    GROUP BY date, bioguide_id
    ORDER BY date, bioguide_id) as votes_missed_df
    left join (select date, 
    count(distinct(roll_id)) as total_votes
    from congressional_votes_tbl
    GROUP BY date
    ORDER BY date) as total_votes
    on votes_missed_df.date = total_votes.date) 
    as total_v_missing
    where votes_missed = total_votes
    GROUP BY bioguide_id) as total_days_missed;"""
    df = pd.read_sql_query(query, connection)
    
    query = """
    SELECT DISTINCT bioguide_id
    from current_congress_bio;"""
    df_2 = pd.read_sql_query(query, connection)
    
    """If person has not missed then they wont show up.
    Those reps need to be add."""
    df = pd.merge(df_2, df, how='left', on='bioguide_id')
    df.loc[df['num_days_missed'].isnull(), 'num_days_missed'] = 0

    df.loc[:, 'compared_to_avg'] = df.loc[
        :, 'num_days_missed'].apply(lambda x: x - math.floor(df.loc[:, 'num_days_missed'].mean()))

    ## Set percentil to add context
    x = df['num_days_missed']
    df.loc[:, 'percentile'] = [100 - stats.percentileofscore(x, a, 'strict') for a in x]

    congress_result = get_congress_leader(street, city, zip_code)
    congress_result = pd.DataFrame(congress_result)
    congress_query = ''
    df_2 = pd.DataFrame()
    for bioguide_id in congress_result['bioguide_id']:
        df_2 = df_2.append(df.loc[df['bioguide_id'] == '{}'.format(bioguide_id)])
        
    df_2 = pd.merge(df_2, congress_result[['bioguide_id', 'name', 'party']],
               how='left', on='bioguide_id')

    connection.close()
    return df_2.to_dict(orient='records')

## Get the number of votes your congressperson missed
def get_congress_votes_missed(street, city, zip_code):
    connection = open_connection()

    query = """
    select bioguide_id, count(vote) as missing_votes
    from congressional_votes_tbl
    WHERE lower(vote) = 'not voting'
    GROUP BY bioguide_id;"""
    df = pd.read_sql_query(query, connection)
    
    query = """
    SELECT DISTINCT bioguide_id
    from current_congress_bio;"""
    df_2 = pd.read_sql_query(query, connection)
    
    """If person has not missed then they wont show up.
    Those reps need to be add."""
    df = pd.merge(df_2, df, how='left', on='bioguide_id')
    df.loc[df['missing_votes'].isnull(), 'missing_votes'] = 0
    
    df.loc[:, 'compared_to_avg'] = df.loc[
        :, 'missing_votes'].apply(lambda x: x - math.floor(df.loc[:, 'missing_votes'].mean()))
    x = df['missing_votes']
    df.loc[:, 'percentile'] = [100 - stats.percentileofscore(x, a, 'strict') for a in x]
    
    congress_result = get_congress_leader(street, city, zip_code)
    congress_result = pd.DataFrame(congress_result)
    congress_query = ''
    df_2 = pd.DataFrame()
    for bioguide_id in congress_result['bioguide_id']:
        df_2 = df_2.append(df.loc[df['bioguide_id'] == '{}'.format(bioguide_id)])
        
    df_2 = pd.merge(df_2, congress_result[['bioguide_id', 'name', 'party']],
                   how='left', on='bioguide_id')
    connection.close()
    return df_2.to_dict(orient='records')


def get_senate_days_missed(zip_code):
    connection = open_connection()

    query = """
    select *
    from
    (select member_full, 
    count(votes_missed) as num_days_missed
    from
    (select votes_missed_df.*, 
    total_votes.total_votes
    from (select date, member_full, count(distinct(roll_id)) as votes_missed
    from senator_votes_tbl
    where lower(vote_cast) = 'not voting'
    GROUP BY date, member_full
    ORDER BY date, member_full) as votes_missed_df
    left join (select date, 
    count(distinct(roll_id)) as total_votes
    from senator_votes_tbl
    GROUP BY date
    ORDER BY date) as total_votes
    on votes_missed_df.date = total_votes.date) 
    as total_v_missing
    where votes_missed = total_votes
    GROUP BY member_full) as total_days_missed;"""
    df = pd.read_sql_query(query, connection)

    
    query = """
    select DISTINCT member_full
    from current_senate_bio;"""
    df_2 = pd.read_sql_query(query, connection)
    
    """If person has not missed then they wont show up.
    Those reps need to be add."""
    df = pd.merge(df_2, df, how='left', on='member_full')
    df.loc[df['num_days_missed'].isnull(), 'num_days_missed'] = 0

    df.loc[:, 'compared_to_avg'] = df.loc[
        :, 'num_days_missed'].apply(lambda x: x - math.floor(df.loc[:, 'num_days_missed'].mean()))
    x = df['num_days_missed']
    df.loc[:, 'percentile'] = [100 - stats.percentileofscore(x, a, 'strict') for a in x]

    senator_result = get_senator(zip_code)
    senator_result = pd.DataFrame(senator_result)
    df_2 = pd.DataFrame()
    for member_full in senator_result['member_full']:
        df_2 = df_2.append(df.loc[df['member_full'] == '{}'.format(member_full)])
        
    df_2 = pd.merge(df_2, senator_result[['member_full', 'first_name',
                                          'last_name', 'party']],
                   how='left', on='member_full')
    connection.close()
    return df_2.to_dict(orient='records')


## Get the number of votes your congressperson missed
def get_senate_votes_missed(zip_code):
    connection = open_connection()

    query = """
    select member_full, count(vote_cast) as missing_votes
    from senator_votes_tbl
    WHERE lower(vote_cast) = 'not voting'
    GROUP BY member_full;"""
    df = pd.read_sql_query(query, connection)
    
    query = """
    select DISTINCT member_full
    from current_senate_bio;"""
    df_2 = pd.read_sql_query(query, connection)
    
    """If person has not missed then they wont show up.
    Those reps need to be add."""
    df = pd.merge(df_2, df, how='left', on='member_full')
    df.loc[df['missing_votes'].isnull(), 'missing_votes'] = 0
    
    df.loc[:, 'compared_to_avg'] = df.loc[
        :, 'missing_votes'].apply(lambda x: x - math.floor(df.loc[:, 'missing_votes'].mean()))
    x = df['missing_votes']
    df.loc[:, 'percentile'] = [100 - stats.percentileofscore(x, a, 'strict') for a in x]
    
    senator_result = get_senator(zip_code)
    senator_result = pd.DataFrame(senator_result)
    df_2 = pd.DataFrame()
    for member_full in senator_result['member_full']:
        df_2 = df_2.append(df.loc[df['member_full'] == '{}'.format(member_full)])
        
    df_2 = pd.merge(df_2, senator_result[['member_full', 'first_name',
                                          'last_name', 'party']],
                   how='left', on='member_full')
    connection.close()
    return df_2.to_dict(orient='records')


"""I'm trying to depricate the google api
so I've build these functions to get away from it"""
def get_senator_user_builder(state_short):
    connection = open_connection()
    sql_command = """
    select * 
    from current_senate_bio
    where lower(state) = lower('{}');""".format(state_short)
    
    senator_result = pd.read_sql_query(sql_command, connection)
    connection.close()
    return senator_result.to_dict(orient='records')

def get_congress_leader_user_builder(street, city, state_short, state_long):
    connection = open_connection()
    district = get_district_from_address(street, city, state_short, state_long)

    sql_command = """
    select * 
    from current_congress_bio
    where state = '{}'
    and ({});""".format(state_long, district)
    congress_result = pd.read_sql_query(sql_command, connection)
    connection.close()
    return congress_result.to_dict(orient='records')

"""Hash password"""
# def password_hasing(password):
#     ## for password hashing
#     import hashlib, uuid
#     salt = uuid.uuid4().hex
#     hashed_password = hashlib.sha512(password + salt).hexdigest()
#     return hashed_password

def hash_password(password, version=1, salt=None):
    import hashlib, uuid
    if version == 1:
        if salt == None:
            salt = uuid.uuid4().hex[:16]
        hashed = salt + hashlib.sha1( salt + password).hexdigest()
        # generated hash is 56 chars long
        return hashed
    # incorrect version ?
    return None

def test_password(password, hashed, version=1):
    import hashlib, uuid
    if version == 1:
        salt = hashed[:16]
        rehashed = hash_password(password, version, salt)
        return rehashed == hashed
    return False

"""Functions to create user info and put into sql"""
 
def create_user_params(email, password, first_name, last_name, gender, dob, street, zip_code):
    import pandas as pd

    """Hold data about the user. We've collected all of the information we need from the
    user. The last thing that needs to be done is to find out what state they live in, and which 
    district they are from. Then we can find their Presenent reps from that info."""
    
    search = ZipcodeSearchEngine()
    zipcode = search.by_zipcode(str(zip_code))

    df = pd.DataFrame(columns=[['email', 'password', 'first_name', 
        'last_name', 'gender', 'dob', 'street', 'zip_code', 'city',
        'state_short', 'state_long', 'district']])

    df.loc[0, 'email'] = email
    df.loc[0, 'password'] = hash_password(password)
    df.loc[0, 'first_name'] = first_name.lower().title()
    df.loc[0, 'last_name'] = last_name.lower().title()
    df.loc[0, 'gender'] = gender.lower().title()
    df.loc[0, 'dob'] = pd.to_datetime(dob)
    df.loc[0, 'street'] = street.lower().title()
    df.loc[0, 'zip_code'] = str(zip_code)
    df.loc[0, 'city'] = str(zipcode['City'].lower().title())
    df.loc[0, 'state_short'] = str(zipcode['State'])
    df.loc[0, 'state_long'] = str(us.states.lookup(df.loc[0, 'state_short']))
    df.loc[0, 'district'] = get_district_from_address(street, df.loc[0, 'city'], df.loc[0, 'state_short'],
                                                      df.loc[0, 'state_long'])

    return df

def user_info_to_sql(df):
    connection = open_connection()
    x = list(df.loc[0,])
    cursor = connection.cursor()

    for p in [x]:
        format_str = """
        INSERT INTO user_tbl (
        email,
        password,
        street,
        zip_code,
        city,
        state_short,
        state_long,
        first_name,
        last_name,
        gender,
        dob,
        district)
        VALUES ('{email}', '{password}', '{street}', '{zip_code}', '{city}', '{state_short}',
                '{state_long}', '{first_name}', '{last_name}', 
                '{gender}', '{dob}', '{district}');"""


    sql_command = format_str.format(email=df.loc[0, 'email'], 
        password=df.loc[0, 'password'], street=df.loc[0, 'street'], 
        zip_code=int(df.loc[0, 'zip_code']), city=df.loc[0, 'city'], 
        state_short=df.loc[0, 'state_short'], 
        state_long=df.loc[0, 'state_long'],  
        first_name=df.loc[0, 'first_name'], 
        last_name=df.loc[0, 'last_name'], 
        gender=df.loc[0, 'gender'], 
        dob=df.loc[0, 'dob'], 
        district=int(df.loc[0, 'district']))


    try:
        cursor.execute(sql_command)
        connection.commit()
        user_made = True
    except IntegrityError as e:
        """duplicate key value violates unique constraint "user_tbl_user_name_key"
        DETAIL:  Key (user_name)=(user_test) already exists."""
        connection.rollback()
        user_made = False
    connection.close()
    return user_made

"""Check if passwords match for login process"""
def search_user_name(user_name):
    connection = open_connection()
    sql_command = """
    select password from  user_tbl
    where email = '{}'""".format(user_name)

    user_results = pd.read_sql_query(sql_command, connection)
    connection.close()
    return user_results

def search_user(user_name, password):
    try:
        password_found = search_user_name(user_name).loc[0, 'password']
        pw_match = test_password(password, password_found, version=1)
        if pw_match == True:
            return True
        elif pw_match == False:
            return False
    except KeyError:
        return "user does not exist"

def get_user_data(user_name):
    connection = open_connection()
    sql_command = """
    select * from  user_tbl
    where email = '{}'""".format(user_name)

    user_results = pd.read_sql_query(sql_command, connection)
    connection.close()
    return user_results