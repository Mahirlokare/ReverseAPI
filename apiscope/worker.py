"""Celery worker configuration; Redis is required only when background jobs are used."""
import os
from celery import Celery
broker=os.getenv("REDIS_URL","redis://localhost:6379/0")
celery_app=Celery("apiscope",broker=broker,backend=broker)
celery_app.conf.update(task_serializer="json",result_serializer="json",accept_content=["json"],task_track_started=True)
@celery_app.task
def analyze_har_task(har):
    from apiscope.core.mvp_analysis import parse_har,summarize
    return summarize(parse_har(har))
