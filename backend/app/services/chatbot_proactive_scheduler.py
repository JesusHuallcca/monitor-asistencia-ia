"""Un planificador servidor; las acciones se conservan en tablas propias, sin pickles."""
from contextlib import nullcontext
from app.services.chatbot_proactive import tick

def make_scheduler(sessions,*,background=False,seconds=30,guard=None):
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler
    scheduler=(BackgroundScheduler if background else BlockingScheduler)(timezone="UTC")
    def run():
        try:
            with guard if guard is not None else nullcontext():return tick(sessions)
        except Exception:
            import logging
            logging.getLogger("monitor.chatbot.proactive").error("proactive_scheduler_failed code=storage_unavailable")
            return {"errors":1}
    scheduler.add_job(run,"interval",seconds=seconds,id="proactive-db-poll",replace_existing=True,coalesce=True,max_instances=1,misfire_grace_time=60)
    return scheduler
