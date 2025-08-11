from celery.schedules import crontab

# 时区
timezone = 'Asia/Shanghai'
enable_utc = True

# 任务路由
task_routes = {
    'app.tasks.scan_tasks.*': {'queue': 'scan'},
    'app.tasks.report_tasks.*': {'queue': 'report'},
}

# 定时任务
beat_schedule = {
    'run-daily-scan': {
        'task': 'app.tasks.scan_tasks.run_batch_scan',
        'schedule': crontab(hour=1, minute=30),  # 每天凌晨1:30执行
        'args': (['example.com', 'example.org'],)
    },
}