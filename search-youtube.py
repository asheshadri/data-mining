'''
Reference the samples here: https://github.com/youtube/api-samples/tree/master/python
trial-app-882cf8779946.json for all resources
go here for API docs: https://google-api-client-libraries.appspot.com/documentation/youtube/v3/python/latest/
'''

#!/usr/bin/python

'''
This program will find videos in youtube relevant to the search term and get all comments for the video and store it in the output file. 
'''
import argparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
import os
import sys
import csv

from googleapiclient.discovery import build_from_document
from googleapiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

## get developer key
DEVELOPER_KEY = ''
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def list_captions(youtube,videoId):
    results = youtube.captions().list(
          part='id,snippet',
          videoId = videoId
    ).execute()
    return(results["items"])

def list_comments(youtube,videoId):
    results = youtube.commentThreads().list(
          part='id,snippet',
          videoId = videoId
    )#.execute()
    return(results)

def download_captions(youtube,id):
    results = youtube.captions().download(
        id = id,
        tfmt='vtt'
    ).execute()
    return results

def get_next_page_videos(youtube,token):
    results = youtube.search().list(
        part ='id,snippet',
        pageToken=token
    ).execute()
    return results

def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
    message="Add a client secret file!")

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

  # if credentials is None or credentials.invalid:
  #   credentials = run_flow(flow, storage, args)

  # Trusted testers can download this discovery document from the developers page
  # and it should be in the same directory with the code.
  # download this from https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest
    with open("youtube-v3-api-captions.json", "r") as f:
        doc = f.read()
        return build_from_document(doc, http=credentials.authorize(httplib2.Http()))

CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"

args = argparser.parse_args()
data = []


def youtube_search(options):
    i = 0
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    # add start date and end date
    req = youtube.search().list(
        q=options.q,
        part='id,snippet',
        maxResults=options.max_results,
        publishedAfter='2017-09-18T00:00:00Z',
        publishedBefore='2018-09-20T00:00:00Z'
    )
    while (req):
        # i = 1
        # while (i):
        #     print(i,'this is i.......')
        search_response = req.execute()
        req = youtube.search().list_next(req, search_response)

        videos = []
        channels = []
        playlists = []

        URL = 'https://www.youtube.com/watch?v='
        # Add each result to the appropriate list, and then display the lists of
        # matching videos, channels, and playlists.
        print("Total results: " + str(search_response["pageInfo"]["totalResults"]))
        print(search_response, 'these are the results')
        ## Work on returning all results
        for search_result in search_response.get('items', []):
            try:
                if search_result['id']['kind'] == 'youtube#video':
                    temp = search_result['snippet']
                    print(URL + search_result['id']['videoId'],
                          temp['title'])  # temp['thumbnails']['channelTitle'] check why this won't work
                    videoID = search_result['id']['videoId']
                    print(search_result)
                    youtube_auth = get_authenticated_service()

                    try:
                        req1 = list_comments(youtube_auth, videoID)
                        while (req1):
                            comment_list = req1.execute()
                            for comment in comment_list["items"]:
                                print(
                                    "Author: " + comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"] + \
                                    "    Comment: <" + comment["snippet"]["topLevelComment"]["snippet"][
                                        "textOriginal"] + \
                                    ">  date: " + comment["snippet"]["topLevelComment"]["snippet"]["publishedAt"])
                                data.append({
                                    "Author": comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                    "Comment": comment["snippet"]["topLevelComment"]["snippet"]["textOriginal"],
                                    "Commment_Date": comment["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                                    "Video_Title": temp['title'],
                                    "Video_URL": URL + search_result['id']['videoId'],
                                    "Video_Upload_Date": temp["publishedAt"]
                                })
                            req1 = youtube_auth.comments().list_next(req1, comment_list)

                    except Exception as e:
                        print(e)
                        continue
                i += 1
            except Exception as e:
                print(e)
                break
    return data

  # for all these videos, get captions and comments- related to MS drug gilenya only.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default='gilenya')
    parser.add_argument('--max-results', help='Max results', default=50)
    args = parser.parse_args()

    try:
        data = youtube_search(args)
        print(data)
        keys = data[0].keys()
        with open('./output/Youtube_gilenya_results.csv', 'w') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
    except HttpError as e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))