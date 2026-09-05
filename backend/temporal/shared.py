"""
Constantes compartidas entre el Worker (temporal/worker.py) y el código
de la app FastAPI que arranca/señaliza workflows (app/core/temporal_client.py).

Separado en su propio módulo para no duplicar el literal de la task
queue en los dos lugares y terminar con un desfasaje silencioso.
"""

TASK_QUEUE = "hospital-task-queue"
