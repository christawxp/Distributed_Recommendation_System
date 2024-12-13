# from dotenv import load_dotenv
import requests
import os
import pickle
import json

# load_dotenv()
# API_KEY = os.getenv('X_RapidAPI_Key_CB')
# HEADERS = {'X-RapidAPI-Key': API_KEY,
#            'X-RapidAPI-Host': 'medium2.p.rapidapi.com'}


def get_user_id(username: str, headers: dict = None) -> str:
    """
    Return medium user_id for the input username

    Parameters:
    - username (str): The medium username of the user

    Returns:
    - user_id (str): The unique user_id of the user
    """

    url = f"https://medium2.p.rapidapi.com/user/id_for/{username}"

    response = requests.get(url, headers=headers,
                            timeout=300)

    try:
        json_data = response.json()
        print(json_data)
        return json_data['id']
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error parsing JSON: {e}")
        return None


def user_id_list(username_list: list) -> list:
    """
    Return the list of user_ids for the list of usernames

    Parameters:
    - username_list (list): The list of usernames

    Returns:
    - user_id_list (list): The list of user_ids for the usernames
    """
    user_list = list()
    for username in username_list:
        user_list.append(get_user_id(username))

    return user_id_list


def get_followers_data(writer_username: str,
                       after_follower_id: str = None,
                       count: int = 25,
                       headers: dict = None) -> dict:
    """
    For a writers username returns their followers user ids

    Parameters:
    - writer_username (str): Username of the writer
    - after_follower_id (int): Get the next 25

    Return:
    - writer_data (dict):
    """

    url = f"https://medium2.p.rapidapi.com/user/{writer_username}/followers"

    if after_follower_id is None:
        querystring = {"count": str(count)}
    else:
        querystring = {"count": str(count),
                       "after": after_follower_id}

    response = requests.get(url, headers=headers,
                            params=querystring, timeout=300)

    try:
        writer_data = response.json()
        return writer_data
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error parsing JSON: {e}")
        return None


def get_top_writers(story_field: str, count: int = 50,
                    headers=None) -> list:
    """
    For a specific area of interest, return the user_ids of the top writers
    as ranked by Medium.

    Parameters:
    - story_field (str): string that represents the field
        (examples: machine-learning, artificial-intelligence,
        data-science)
    - count (int) - the number of writer user_ids to return
    - headers - the API headers to use in the API request

    Returns:
    - writer_ids
    """
    # set the url using the story field
    url = f"https://medium2.p.rapidapi.com/top_writers/{story_field}"

    querystring = {"count": f"{str(count)}"}

    response = requests.get(url, headers=headers,
                            params=querystring, timeout=300)

    writer_ids = response.json()
    return writer_ids['top_writers']


def get_user_info(user_id: str, headers=None) -> dict:
    """
    For a specific user, return personal information about the writer,
        including name, bio, followers and follower count.

    Parameters:
    - user_id (str) - the user_id that will contain the relevant personal
        information of the writer.
    - headers - the API headers to use in the API request

    Returns:
    - writer_ids
    """
    url = f"https://medium2.p.rapidapi.com/user/{user_id}"

    response = requests.get(url, headers=headers,
                            timeout=300)

    user_info = response.json()
    return user_info


def retrieve_writer_followers(writer_info: dict, query_count: int):
    """
    Retrieves followers of a writer and updates the writer's information.

    Parameters:
    - writer_info (dict): Dictionary containing writer information, including
                          'id' and optional 'followers' list.
    - query_count (int): Number of queries to be made to retrieve
                         follower data.

    Returns:
    - None

    The function makes queries to retrieve follower information for the
    specified writer and updates the 'followers' key in the provided
    'writer_info' dictionary.

    It retrieves followers in chunks determined by the 'query_count' parameter,
    and updates the 'after_follower_id' for subsequent queries.

    If the writer_info dictionary already contains a 'followers' list,
    the function retrieves the last follower id from the list and
    uses it as the starting point for subsequent queries. The function
    stops when the specified number of queries ('query_count') is
    reached or when there is no more follower data available.
    """
    # initialize last follower variable and writer_id
    after_follower_id = None
    writer = writer_info['id']
    # check to see if writer already has a list of follower ids
    followers = writer_info.get('followers', None)
    # if there are followers for the writer, retrieve the last follower id
    if followers:
        after_follower_id = followers[-1]
    # make queries and add followers to writer's information
    for i in range(query_count):
        if after_follower_id is None:
            follower_info = get_followers_data(writer_username=writer)
            after_follower_id = follower_info['next']
            writer_info['followers'] = follower_info['followers']
        else:
            response = get_followers_data(writer_username=writer,
                                          after_follower_id=after_follower_id)
            if response is None:
                print(f'Stopped at {i*25} followers')
                break
            after_follower_id = response['next']
            writer_info['followers'] += response['followers']


def get_top_articles(writer_id: str, headers=None) -> list:
    """
    Retrieve the top articles written by a Medium user.

    Parameters:
    - writer_id (str): Unique identifier for the Medium writer.
    - headers (dict): Headers to be included in the HTTP request
                      (default: global 'headers').

    Returns:
    list: A list containing the top articles written by the specified user.

    This function sends an HTTP GET request to the Medium API endpoint for
    retrieving the top articles written by a user with the given 'writer_id'.
    The request includes optional headers, with the default headers provided
    by the 'headers' parameter.

    The function then parses the JSON response and returns a dictionary
    containing information about the top articles, including details such
    as title, publication date, and other relevant metadata.

    Note: Ensure that the 'headers' parameter includes any required
    authentication or authorization information for accessing the Medium API.
    """
    url = f"https://medium2.p.rapidapi.com/user/{writer_id}/top_articles"
    response = requests.get(url=url, headers=headers,
                            timeout=300)
    articles = response.json()
    return articles['top_articles']


def get_article_info(article: str, headers=None) -> dict:
    """
    Retrieve information for a specific Medium article.

    Parameters:
    - article_id (str): Unique identifier for the Medium article.
    - headers (dict): Headers to be included in the HTTP request
                      (default: global 'headers').

    Returns:
    dict: A dictionary containing information about the specified Medium
          article.

    This function sends an HTTP GET request to the Medium API endpoint for
    retrieving information about a specific article with the given
    'article_id'. The request includes optional headers, with the default
    headers provided by the 'headers' parameter.

    The function then parses the JSON response and returns a dictionary
    containing detailed information about the specified article,
    including metadata such as title, author, publication date, and content.

    Note: Ensure that the 'headers' parameter includes any required
    authentication or authorization information for accessing the Medium API.
    """
    url = f"https://medium2.p.rapidapi.com/article/{article}"
    try:
        response = requests.get(url=url, headers=headers,
                                timeout=300)
        response.raise_for_status()  # Raise HTTPError for bad responses
        info = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error retrieving article information: {e}")
        info = {}
    return info


def get_article_content(article_id: str,
                        headers: dict = None) -> dict:
    """
    Retrieve the content of a specific Medium article.

    Parameters:
    - article_id (str): Unique identifier for the Medium article.
    - headers (dict): Headers to be included in the HTTP request
                      (default: global 'headers').

    Returns:
    dict: A dictionary containing the content of the specified Medium
          article. Returns an empty dictionary if there is an
          issue with the response format.

    This function sends an HTTP GET request to the Medium API endpoint
    for retrieving the content of a specific article with the
    given 'article_id'. The request includes optional headers, with the
    default headers provided by the 'headers' parameter.

    The function attempts to parse the JSON response and returns
    a dictionary containing the content of the specified article,
    including text, images, and other details.

    If there is an issue with the response format, the function
    catches the exception, prints an error message, and returns
    an empty dictionary.

    Note: Ensure that the 'headers' parameter includes any required
    authentication or authorization information for accessing the Medium API.
    """
    url = f"https://medium2.p.rapidapi.com/article/{article_id}/content"
    try:
        response = requests.get(url=url, headers=headers,
                                timeout=300)
        response.raise_for_status()  # Raise HTTPError for bad responses
        article_content = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error retrieving article information: {e}")
        article_content = {}
    return article_content


def get_article_list(writer_id: str, top_articles: bool = False,
                     headers: dict = None) -> list:
    """
    Retrieve a list of articles associated with a Medium writer.

    Parameters:
    - writer_id (str): Unique identifier for the Medium writer.
    - top_articles (bool): Flag indicating whether to retrieve
                           only top articles (default: False).
    - headers (dict): Headers to be included in the HTTP request
                      (default: global 'headers').

    Returns:
    - list: A list of dictionaries, each containing information about
            a Medium article.

    This function retrieves a list of articles associated with a Medium
    writer using the provided 'writer_id'. The list can include top articles
    or all articles based on the 'top_articles' parameter.

    If 'top_articles' is True, the function retrieves the article ids
    for the writer's top articles and then fetches detailed information,
    including content, for each article.

    If 'top_articles' is False, the function retrieves the article ids
    for all articles associated with the writer and then fetches detailed
    information, including content, for each article.

    The function limits the number of articles retrieved to a maximum of 200
    to manage query size.

    Note: Ensure that the 'headers' parameter includes any required
    authentication or authorization information for accessing the Medium API.
    """
    # retrieve the article ids for the top articles
    if top_articles:
        url = f"https://medium2.p.rapidapi.com/user/{writer_id}/top_articles"
        response = requests.get(url=url, headers=headers, timeout=300)
        response = response.json()
        articles = response['top_articles']
    # retrieve the article ids for all articles
    else:
        article_url = f"https://medium2.p.rapidapi.com/user\
                        /{writer_id}/articles"
        response = requests.get(article_url, headers=headers, timeout=300)
        response = response.json()
        try:
            articles = response['associated_articles']
        except KeyError as e:
            print(f"Error parsing JSON: {e}")
            return list()
    article_list = list()
    # set length of article list to limit queries
    check_len = min(200, len(articles))
    for art in articles[:check_len]:
        # retrieve info on each article
        info = get_article_info(article=art, headers=headers)
        # add article content to the info document
        content = get_article_content(article_id=art, headers=headers)
        info['content'] = content
        # add article information to article list
        article_list.append(info)
    return article_list


def get_all_writer_info(writer_ids: list, headers: dict,
                        follower_query_count: int = 200):
    """
    Retrieve comprehensive information about Medium writers, including
    user details, followers, top articles, and article content.

    Parameters:
    - writer_ids (list): List of Medium user IDs for which to retrieve
                         information.
    - headers (dict): Headers to be included in the HTTP requests
                      (default: global 'HEADERS').

    Returns:
    list: A list of dictionaries, each containing comprehensive information
          about a Medium writer. Each dictionary includes details such as
          user information, followers, top articles, and article content.

    This function iterates through the provided list of Medium user IDs
    ('writer_ids'). For each user, it retrieves user details, followers,
    top articles, and article content. The information is organized into
    dictionaries, and a list of these dictionaries is returned.

    Note: Ensure that the 'headers' parameter includes any required
    authentication or authorization information for accessing the Medium API.
    """
    # take the top writers of a field from Medium
    # writer_ids = get_top_writers(story_field=field, headers=headers)
    ### TODO
    '''
    Implement check to see if top writers have changed at all
    '''
    # initialize a list to track writer information dictionaries
    writer_list = list()
    # iterate through top writer ids to retrieve their information
    for writer in writer_ids:
        writer_info = get_user_info(writer, headers=headers)
        # retrieve the followers for each writer
        retrieve_writer_followers(writer_info=writer_info,
                                  query_count=follower_query_count)
        # retrieve dictionary of top articles from each of the writers
        top_articles = get_article_list(writer, top_articles=True,
                                        headers=headers)
        articles = get_article_list(writer, top_articles=False,
                                    headers=headers)
        writer_info['articles'] = articles
        writer_info['top_articles'] = top_articles
        writer_list.append(writer_info)
        '''
        Implement check to see if articles have changed at all/update clap
        counts for articles in writer dictionaries
        '''
    return writer_list


def get_follower_table(writer_info_list: list) -> list:
    """
    Creates a table of common followers for a list of writers.

    Parameters:
    - writer_info_list (list): A list of dictionaries containing
                               writer information.
      Each dictionary should have a 'followers' key representing a list
      of follower IDs.

    Returns:
    dict: A dictionary where keys are follower IDs, and values are
          lists of writers who have that follower in common.
    """
    common_followers = dict()
    for writer in writer_info_list:
        followers = writer['followers']
        for follower in followers:
            if common_followers.get(follower, None):
                common_followers[follower].append(writer)
            else:
                common_followers[follower] = [writer]
    return common_followers


def check_top_writers(headers: dict) -> list:
    writer_set = set()
    for i, topic in enumerate(['data-science', 'machine-learning',
                               'artificial-intelligence']):
        topics = ['data-science', 'machine-learning', 'artificial-intelligence']
        writers = get_top_writers(story_field=topic, count=50,
                                  headers=headers)
        j = 0
        print(f'Adding writers from {topics[i]}')
        while len(writer_set) < (i + 1) * 10:
            writer_set.add(writers[j])
            j += 1
            if j >= len(writers):
                break
    return list(writer_set)
