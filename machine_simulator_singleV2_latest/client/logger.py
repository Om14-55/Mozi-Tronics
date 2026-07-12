import time, logging

def write_to_logger(log_queue, queue_lock, stop_event):
    while not (stop_event.is_set() and len(log_queue) == 0):
        # if stop_event.is_set() and len(log_queue) == 0:
        #     break
        if log_queue:
            with queue_lock:
                data = log_queue.pop()
        else:
            data = None
            time.sleep(0.01)

        if data:
            logging.info(f"\nClient Code: {data.ClientCode} \nProduct Code: {data.PCode} \nProduct Name: {data.PName} \nFactory Code: {data.FactCode} \nLine Number: {data.LineNo} \nBatch Number: {data.BatchNo} \nUpper Threshold: {data.UpperThreshold} \nLower Threshold: {data.LowerThreshold} \nWeight: {data.Weight}\n")