# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .merge import main as merge_main
from .auto_replace_tag import main as auto_replace_tag_main
from .revision import main as revision_main

__homepage__ = 'https://github.com/NAL-i5K/GFF3toolkit'
__all__ = ['merge_main', 'auto_replace_tag_main', 'revision_main']
