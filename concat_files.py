import os
import json
import gzip
import logging
import argparse
import csv
from tempfile import NamedTemporaryFile
import shutil
from datetime import datetime, timedelta

TASKS = "concat_files.csv"


def next_task():
    tempfile = NamedTemporaryFile(mode="a+", delete=False)
    with open(TASKS, "r+") as f, tempfile:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        writer = csv.writer(tempfile, delimiter=";", quotechar='"')
        next_task = ""
        for row in reader:
            logging.info(row)
            if int(row[1]) != 0:
                writer.writerow(row)
            else:
                if next_task != "":
                    writer.writerow(row)
                else:
                    row[1] = 1
                    next_task = row[0]
                    writer.writerow(row)
    shutil.move(tempfile.name, TASKS)
    logging.info("next task: {}".format(next_task))
    return next_task


def deduplicate(tweet_dict, tweet_list, batch):
    for tweet in batch:
        if "delete" in tweet[2]:
            tweet_list.append(tweet)
            continue
        elif ("limit" in tweet[2]) or ("status_withheld" in tweet[2]) or ("user_withheld" in tweet[2]):
            tweet_list.append(tweet)
            continue
        try:
            if tweet[2]["id"] not in tweet_dict:
                tweet_dict[tweet[2]["id"]] = {}
                tweet_dict[tweet[2]["id"]][tweet[2]["tags"][0]] = tweet
            else:
                tweet_dict[tweet[2]["id"]][tweet[2]["tags"][0]] = tweet
        except KeyError:
            logging.error(tweet[2].keys())
    return tweet_list, tweet_dict


def write_tweets(tweets, path):
    with gzip.open(path + ".gz", 'ab') as outputfile:
        for data in tweets:
            json_str = json.dumps(data) + "\n"
            json_bytes = json_str.encode('utf-8')
            outputfile.write(json_bytes)


def concat_files(path, task):
    day = "/".join(task.split("-"))
    for dirName, subdirList, fileList in sorted(os.walk(path + day)):
        if fileList != [] and dirName != path:
            logging.info(dirName)
            for file in fileList:
                file_path = dirName + "/" + file
                with gzip.open(file_path, mode='rb') as f:
                    try:
                        tweets = (json.loads(line.decode('utf-8')) for line in f)
                        write_tweets(tweets, path + day[0:8] + task)
                    except Exception as e:
                        logging.error(str(e) + " " + file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=False, default="/usr/src/app/data/tweets/", help='Path to tweets storage folder')

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)
    # task = next_task()
    task = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    logging.info(task)
    concat_files(args.path, task)
