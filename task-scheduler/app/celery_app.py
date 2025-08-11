from celery import Celery

# 创建 Celery 实例
celery_app = Celery(
    'task_scheduler',
    broker='amqp://guest:guest@localhost:5672//',
    backend='redis://localhost:6379/0',
    include=['app.tasks.scan_tasks', 'app.tasks.report_tasks', 'app.tasks.cleanup_tasks']
)

# 从配置文件加载配置
celery_app.config_from_object('app.config.celery_config')

if __name__ == '__main__':
    celery_app.start()