from __future__ import annotations

from datetime import date
from typing import List, Optional, Dict, Any
from math import ceil

import django
from django.utils import timezone
django.setup()  # Ensures Django is initialized when FastAPI imports models.

from django.db import transaction
# from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ..models import DailyPost, DailyDevotion
from ..schemas import DailyPostOut, DailyDevotionOut
from ..utils import parse_tsv_bytes
from asgiref.sync import sync_to_async
from fastapi import Query
from ..fastapi_app import api

