#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import sys
import os
for p in sys.path:
    if "hydro4x2" in p and "Sod" in p:
        sys.path.insert(0, os.path.join(p, '../'))
        break

from xSod import *
