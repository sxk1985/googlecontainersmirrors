#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author by xiexianbin@yovole.com
# function: sync google containers registory to docker.com.
# date 2018-3-10

##
# EVN
# DOCKER_USER=xiexianbin
# DOCKER_PASSPORT=password
##
import json
import logging
import os
import requests
import subprocess
import sys
import urllib2

## start log
# create logger
log_level = logging.DEBUG
formatter = logging.Formatter(
    fmt="%(asctime)-15s %(levelname)s %(process)d %(message)s - %(filename)s %(lineno)d",
    datefmt="%a %d %b %Y %H:%M:%S")

logger = logging.getLogger(name="googlecontainersmirrors")
logger.setLevel(log_level)

fh = logging.FileHandler(filename="googlecontainersmirrors.log")
fh.setLevel(log_level)
fh.setFormatter(formatter)
logger.addHandler(fh)

oh = logging.StreamHandler(sys.stdout)
oh.setLevel(log_level)
oh.setFormatter(formatter)
logger.addHandler(oh)
## end log

# define file path
GCR_IMAGES = "https://raw.githubusercontent.com/xiexianbin/googlecontainersmirrors/sync/googlecontainersmirrors.txt"

GH_TOKEN=1
GIT_USER="xiexianbin"
GIT_REPO="googlecontainersmirrors"
DOCKER_REPO=GIT_REPO

DOCKER_TAGS_API_URL_TEMPLATE = {
    "docker.com": "https://registry.hub.docker.com/v1/repositories/%(repo)s/%(image)s/tags",
    "gcr.io": "https://gcr.io/v2/%(repo)s/%(image)s/tags/list"
}

ENV = os.environ


def _bash(command, force=False, debug=False):
    args = ['bash', '-c', command]

    _subp = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = _subp.communicate()
    returncode = _subp.poll()
    logger.debug("Run bash: %s, ret is %s, stderr is: %s"
                 % (command, returncode, stderr))

    if not stdout and not stderr:
        logger.debug("Run bash: %s, ret is %s" % (command, returncode))

    if force:
        return returncode, stdout, stderr
    return returncode


def _get_images_tags_list(domain, repo, image):
    tags_list = []
    url = DOCKER_TAGS_API_URL_TEMPLATE[domain] % {"repo": repo, "image": image}
    try:
        json_tags = json.load(urllib2.urlopen(url))
    except urllib2.HTTPError as e:
        logger.warn("get url: %s, except: %s"
                    % (url, e.msg))
        return tags_list
    if domain == "docker.com":
        for t in json_tags:
            tags_list.append(t.get("name"))
    elif domain == "gcr.io":
        tags_list = json_tags.get("tags")
    return tags_list


def _get_token():
    headers = {'Content-Type': 'application/json'}
    # data = {
    #     "username": ENV['DOCKER_USER'],
    #     "password": ENV['DOCKER_PASSPORT']}
    data = '{"username": "xiexianbin", "password": "Xie8Xian1Bin8"}'
    url = "https://hub.docker.com/v2/users/login/"
    response = requests.post(url=url, data=data, headers=headers)
    token = response.json().get("token")

    return token


def _del_image_by_tag(image, tag):
    # 1. get token
    token = _get_token()
    headers = {'Authorization': 'JWT %s' % token}
    data = '{"username": "xiexianbin", "password": ""}'
    url = "https://hub.docker.com/v2/repositories/%s/%s/tags/%s/" % (DOCKER_REPO, image, tag)
    try:
        response = requests.delete(url=url, data=data, headers=headers)
    except:
        logger.debug("wrong delete %s:%s, ret : %s"
                     %(image, tag, response))
    logger.debug("%s" % response)


def _do_rm_wrong_order_image_tag():
    for image in urllib2.urlopen(GCR_IMAGES):
        image = image.replace("\n", "")
        # target images tags
        dockerhub_image_tags = _get_images_tags_list("docker.com", DOCKER_REPO, image)

        for tag in dockerhub_image_tags:
            if tag.startswith('v1.10'):
                logger.debug("Begin to delete image: [%s:%s]" % (image, tag))
                # delete docker images
                _del_image_by_tag(image, tag)


def main():
    logger.info("--- Begin to delete wrong order image ---")

    # 2. do delete wrong order image tags
    # _do_rm_wrong_order_image_tag()
    # _get_token()
    # _del_image_by_tag('googlecontainersmirrors/hyperkube',
    #                   'v1.10.0-rc.1')
    _do_rm_wrong_order_image_tag()

    logger.info("--- End to delete wrong order image ---")


if __name__ == '__main__':
    main()
