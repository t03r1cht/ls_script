from bs4 import *
import optparse
import os
import sys
import requests
from time import gmtime, strftime, sleep

# all user posts
user_posts = {}

def main():
    parser = optparse.OptionParser("usage %prog -u <url> -o outfile name (default=outfile)")
    parser.add_option("-u", dest="dest_url", type="string", help="specify ls url")
    parser.add_option("-o", dest="outfile", type="string", help="outfile for user posts")
    (options, args) = parser.parse_args()

    dest_url = options.dest_url
    outfile = options.outfile

    if dest_url == None:
        print(parser.usage)
        exit(0)

    if outfile == None:
        outfile = "outfile"
        log("set filename to default. set custom filename with -o option")

    log("destination url '" + dest_url + "'")

    # build url
    url_parts = dest_url.split("=")

    res = requests.get(dest_url)
    try:
        res.raise_for_status()
    except Exception as e:
        log("something went wrong '" + e + "'")

    soup = BeautifulSoup(res.text, "html.parser")
    posts = soup.find_all("div", {"class": "post-content"})

    # find current page number (start from curr_page and run until the end of the thread
    curr_page = soup.find("span", {"class": "active"})
    log("curr_page=" + str(curr_page.text))

    # find last page number
    all_no = []
    nav_no = soup.find_all("a", {"class": "link"})
    for no in nav_no:
        all_no.append(int(no.text))
    max_page = int(max(all_no))
    log("max_page=" + str(max_page))

    # per 50 iterations, write to file and clean memory
    cycle_count = 0
    file_prefix_time = str(strftime("%H%M%S", gmtime()))

    # for i in range(1, max_page + 1):
    for i in range(1, 1000):
        if i % 50 != 0:
            new_url = url_parts[0] + "=" + str(i)
            resp = get_posts(new_url)
            if resp[0]:
                merge_dics(resp[1])
                log("done  '" + str(i) + "/" + str(max_page) + "' ")
            else:
                log("something failed at'" + str(i) + "/" + str(max_page) + "'")
        else:
            # write to part file
            filename = file_prefix_time + "_" + outfile + ".part" + str(cycle_count)
            cycle_count += 1

            file = open(filename, "w+", encoding="utf-8")

            for post in user_posts:
                username = post;
                post_list = user_posts[post].split(",")
                post_count = len(post_list)
                encoded_str = conv_umlaute(user_posts[post])
                file.write(username + "," + str(post_count) + "," + str(encoded_str) + "\n")
            file.close()

            # free memory
            user_posts.clear()
            log("created part! '" + filename + "'")

    log("merging parts...")
    posts_total = merge_parts(file_prefix_time, cycle_count, outfile)
    log("all parts merged!")

    out_filename = file_prefix_time + "_" + outfile + ".txt"
    file = open(out_filename, "w+", encoding="utf-8")
    for user_post in posts_total:
        post_count = len(posts_total[user_post].split(","))
        file.write(user_post + "," + str(post_count) + "," + posts_total[user_post] + "\n")
    log("posts saved in '" + out_filename + "'")
    log("cleaning up...")
    for i in range(cycle_count):
        os.remove(file_prefix_time + "_" + outfile + ".part" + str(i))
    log("done!")


def get_posts(dest_url):
    res = requests.get(dest_url)
    try:
        res.raise_for_status()
    except Exception as e:
        log("something went wrong '" + e + "'")

    soup = BeautifulSoup(res.text, "html.parser")
    posts = soup.find_all("div", {"class": "post-content"})

    all_names = []
    user_posts = {}

    try:
        for post in posts:
            uname = post.find("a", {"class": "username"})
            post_text = post.find("p")
            if uname.text.split("-")[0] == "gelöscht":
                pass
            else:
                if uname.text in user_posts:
                    user_posts[uname.text] += "," + post_text.text.strip().replace(",", ";")
                else:
                    user_posts[uname.text] = post_text.text.strip().replace(",", ";")
        return [True, user_posts]
    except Exception as e:
        return [False, user_posts]

def merge_dics(new_dic):
    try:
        for post in new_dic:
            if post in user_posts:
                user_posts[post] += "," + new_dic[post]
            else:
                user_posts[post] = new_dic[post]
    except Exception as e:
        log("something failed at merge_dics()")

def merge_parts(file_prefix_time, cycle_count, outfile):
    posts_total = {}
    for i in range(cycle_count):
        filename = file_prefix_time + "_" + outfile + ".part" + str(i)
        file = open(filename, "r", encoding="utf-8")
        text = file.read()
        file.close()
        posts_by_user = text.split("\n")

        for post in posts_by_user:
            user = post.split(",")[0]
            psts = post.split(",")[2:]
            merged_sublist = ",".join(psts)

            if user in posts_total:
                posts_total[user] += "," + merged_sublist
            else:
                posts_total[user] = merged_sublist
        log("completed part" + str(i))
    return posts_total



def conv_umlaute(input):
    text = ''
    for zeichen in input:
        if zeichen == u'ä':
            text += 'ae'
        elif zeichen == u'ö':
            text += 'oe'
        elif zeichen == u'ü':
            text += 'ue'
        elif zeichen == u'ß':
            text += 'ss'
        else:
            text += zeichen
    return text

def log(msg):
    print("[" + str(strftime("%H:%M:%S", gmtime())) + "]" + " " + msg)


if __name__ == '__main__':
    main()