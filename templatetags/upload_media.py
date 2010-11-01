# -*- coding: utf-8 -*-
#getted from http://softwaremaniacs.org/blog/2009/03/22/media-tag/
import os
import urlparse
import traceback
from django import template
from django.conf import settings
from django.utils.encoding import iri_to_uri
from ..view import STORAGE_URL

register = template.Library()

@register.simple_tag
def upload_media(filename, flags=''):
    url = urlparse.urljoin(STORAGE_URL, filename)
    return iri_to_uri(url)
