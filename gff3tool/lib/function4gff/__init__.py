# -*- coding: utf-8 -*-
"""Extract sequences from specific regions of genome based on gff file."""
from __future__ import absolute_import
from .function4gff import (FIX_MISSING_ATTR, extract_internal_detected_errors,
                           featureSort)

__homepage__ = 'https://github.com/NAL-i5K/GFF3toolkit'
__all__ = ['FIX_MISSING_ATTR', 'extract_internal_detected_errors',
           'featureSort']
