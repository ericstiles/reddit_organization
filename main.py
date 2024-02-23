#!/usr/bin/env python3

import praw
import pandas as pd
from datetime import datetime
import os
import argparse

client_id = os.environ['CLIENT_ID']  # Enter your client ID
client_secret = os.environ['CLIENT_SECRET']  # Enter you client secret
username = os.environ['USERNAME']  # Enter Username
password = os.environ['PASSWORD']  # Enter password

parser = argparse.ArgumentParser(description='Organize saved and commented subreddits into generated html files')
parser.add_argument('base', type=str, help='base directory for storing generated html files')
args = parser.parse_args()

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent='Saved posts scraper by /u/' + username,
                     username=username,
                     password=password)

reddit_home_url = 'https://www.reddit.com'
saved_models = reddit.user.me().saved(limit=None)  # models: Comment, Submission
array_subreddits = {}

working_dir = args.base


def cleanup(directory_path):
    try:
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)

        file_list = os.listdir(directory_path)

        for file_name in file_list:
            file_path = os.path.join(directory_path, file_name)
            os.remove(file_path)

        print(f"All files in {directory_path} successfully removed.")
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}")


def get_baseline():
    obj = {
        "array_subr_name": [],
        "array_model_type": [],
        "array_noSfw": [],
        "array_test_url": []}
    return obj


def handle(inner_saved_models):
    for model in inner_saved_models:

        if model.subreddit.display_name not in array_subreddits:
            array_subreddits[model.subreddit.display_name] = get_baseline()

        subreddit = model.subreddit  # Subreddit model that the Comment/Submission belongs to
        subr_name = subreddit.display_name
        url = reddit_home_url + model.permalink

        if isinstance(model, praw.models.Submission):  # if the model is a Submission
            title = model.title
            no_sfw = str(model.over_18)
            model_type = "#Post"
        else:  # if the model is a Comment
            title = model.submission.title
            no_sfw = str(model.submission.over_18)
            model_type = "#Comment"

        array_subreddits[model.subreddit.display_name]['array_test_url'].append(
            '<a href=' + url + ' target="_blank"><div>' + title + '</div></a>')
        array_subreddits[model.subreddit.display_name]['array_model_type'].append(model_type)
        array_subreddits[model.subreddit.display_name]['array_noSfw'].append(no_sfw)
        array_subreddits[model.subreddit.display_name]['array_subr_name'].append(model.subreddit.display_name)


def write_main_page():
    f = open(working_dir + "/index.html", "w")
    f.seek(0)
    f.write("<h1>" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "</h1>")
    f.write("<h2>" + str(len(array_subreddits.keys())) + " subreddits" + "</h2>")

    # Table of subreddits
    f.write("<ul>")

    for i in sorted(array_subreddits.keys()):
        file_name = i + ".html"
        saved_count = "(" + str(len(array_subreddits[i]['array_subr_name'])) + ")"
        nsfw_count = array_subreddits[i]['array_noSfw'].count('True')
        nfsw_name = " | (" + str(nsfw_count) + ")" if nsfw_count > 0 else ""
        subreddit_name = i + " " + saved_count + nfsw_name
        line_item = "<li id=\"top_" + array_subreddits[i]['array_subr_name'][
            0] + "\" ><a href=\"" + file_name + "\">" + subreddit_name + "</a></li>"
        f.write(line_item)

    f.write("</ul>")

    f.truncate()
    f.close()


def write_sub_pages():
    for i in array_subreddits.keys():
        file_name = i + ".html"
        f = open(working_dir + "/" + file_name, "w")
        f.seek(0)

        df = pd.DataFrame({
            "Link": array_subreddits[i]['array_test_url'],
            "model_type": array_subreddits[i]['array_model_type'],
            "noSfw": array_subreddits[i]['array_noSfw']
        })  # initialize dataframe
        #
        f.write(df.to_html(
            render_links=True,
            escape=False,
        ))
        f.truncate()
        f.close()


cleanup(working_dir)
handle(saved_models)
write_main_page()
write_sub_pages()

# unsave: https://www.reddit.com/dev/api/#POST_api_unsave
