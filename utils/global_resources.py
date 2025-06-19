import logging
from azure.monitor.opentelemetry import configure_azure_monitor
from core.settings import Azure_Middleware_InstrumentationKey
from opentelemetry import trace

class global_azure_monitor:
    def __init__(self):
        configure_azure_monitor(
            connection_string= f"InstrumentationKey={Azure_Middleware_InstrumentationKey}"
        )

azure_monitor = global_azure_monitor()
# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Get OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

def create_record_azure_insight(error: Exception,run_id:str,function_name:str):
    logger.error(f'End point: {function_name}: {error} \n run_id: {run_id}', exc_info=True)
    span = tracer.start_span(function_name)
    span.record_exception(error)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(f'{error} / {run_id}')))    
    span.end()        