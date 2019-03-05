#!/usr/bin/env python
from project import celery, create_app

app = create_app(is_testing = None, celery_app = 'celery_worker')
app.app_context().push()