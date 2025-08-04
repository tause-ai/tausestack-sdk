"""
JobManager: Sistema base para jobs y ejecución programada en Tausestack.

Permite registrar y ejecutar jobs (tareas) de forma programada o bajo demanda.
Preparado para integración futura con notificaciones y orquestadores externos.
"""
import threading
import time
from typing import Callable, Dict, Any, Optional

class Job:
    def __init__(self, name: str, func: Callable, schedule: Optional[str] = None, args: tuple = (), kwargs: dict = {}):
        self.name = name
        self.func = func
        self.schedule = schedule  # cron-like string o None para jobs manuales
        self.args = args
        self.kwargs = kwargs
        self.last_run = None
        self.thread = None

    def run(self):
        self.last_run = time.time()
        return self.func(*self.args, **self.kwargs)

class JobManager:
    """Gestor simple de jobs programados o bajo demanda."""
    def __init__(self):
        self.jobs: Dict[str, Job] = {}

    def register(self, name: str, func: Callable, schedule: Optional[str] = None, args: tuple = (), kwargs: dict = {}):
        self.jobs[name] = Job(name, func, schedule, args, kwargs)

    def run(self, name: str):
        if name not in self.jobs:
            raise ValueError(f"Job '{name}' no registrado")
        return self.jobs[name].run()

    def run_async(self, name: str):
        if name not in self.jobs:
            raise ValueError(f"Job '{name}' no registrado")
        job = self.jobs[name]
        t = threading.Thread(target=job.run)
        t.start()
        job.thread = t
        return t

    def list_jobs(self):
        return list(self.jobs.keys())

    def status(self, name: str) -> Dict[str, Any]:
        if name not in self.jobs:
            raise ValueError(f"Job '{name}' no registrado")
        job = self.jobs[name]
        return {
            "name": job.name,
            "last_run": job.last_run,
            "is_alive": job.thread.is_alive() if job.thread else False
        }
