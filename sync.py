#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author by xiexianbin@yovole.com
# function: sync google containers registory to docker.com.
# date 2018-3-10

##
# ENV:
#   1. GH_TOKEN
#   2.
#   3.
##

import json
import logging
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


def _bash(command, force=False, debug=False):
    args = ['bash', '-c', command]

    _subp = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = _subp.communicate()
    returncode = _subp.poll()
    logger.debug("Run bash: %s, ret is %s, stderr is: %s"
                 % (command, returncode, stderr))

    if force:
        return returncode, stdout, stderr
    return returncode


def _init_git():
    _bash('git config user.name "xiexianbin"')
    _bash('git config user.email "me@xiexianbin.cn"')

    # clone master branch
    _bash('git clone "https://%s@github.com/%s/%s.git"'
          % (GH_TOKEN, GIT_USER, GIT_REPO))


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


def _sync_image(source_domain, source_repo,
                target_domain, target_repo,
                image, tag):
    if source_domain == "docker.com":
        if source_repo == "":
            source_image = '%s:%s' % (image, tag)
        else:
            source_image = '%s/%s:%s' % (source_repo, image, tag)
    else:
        source_image = '%s/%s/%s:%s' % (source_domain, source_repo, image, tag)

    if target_domain == "docker.com":
        target_image = '%s/%s:%s' % (target_repo, image, tag)
    else:
        target_image = '%s/%s/%s:%s' % (target_domain, target_repo, image, tag)

    logger.info("begin to sync image from %s to %s"
                % (source_image, target_image))

    # source
    _bash('docker pull %s' % source_image)
    # tag
    _bash('docker tag %s %s' % (source_image, target_image))
    # push
    _bash('docker push %s' % target_image)

    # clean the docker file
    _bash('docker system prune -f -a')


def _do_sync():
    for image in urllib2.urlopen(GCR_IMAGES):
        image = image.replace("\n", "")
        logger.debug("Begin to sync image: [%s]" % image)

        # source images tags
        gcr_image_tags = _get_images_tags_list("gcr.io", "google_containers", image)
        # target images tags
        dockerhub_image_tags = _get_images_tags_list("docker.com", DOCKER_REPO, image)

        for tag in gcr_image_tags:
            if tag in dockerhub_image_tags:
                logger.debug("image: %s:%s, is already sync." % (image, tag))
                continue

            # do sync
            _sync_image("gcr.io", "google_containers",
                        "docker.com", DOCKER_REPO,
                        image, tag)


def main():
    logger.info("--- Begin to sync googlecontainersmirrors ---")

    # 1. copy mirror
    #_init_git()
    #print
    #print

    # 2. do sync
    _do_sync()

    # 3. update


    logger.info("--- End to sync googlecontainersmirrors ---")


if __name__ == '__main__':
    main()
