import sys, configparser, threading, os, logging, random, time, requests
from collections import deque
from checkweigher import checkweigher_machine
from logger import write_to_logger
from db_insert import write_to_db


# LOGGING CONFIGURATION

log_format = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")

client_handler = logging.FileHandler('client_log.log')
client_handler.setLevel(logging.INFO)
client_handler.setFormatter(log_format)

error_handler = logging.FileHandler('error_log.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_format)

execution_handler = logging.FileHandler('execution_log.log')
execution_handler.setLevel(logging.INFO)
execution_handler.setFormatter(log_format)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(client_handler)
root_logger.addHandler(error_handler)

exec_logger = logging.getLogger("execution")
exec_logger.setLevel(logging.INFO)
exec_logger.addHandler(execution_handler)
exec_logger.propagate = False 


def execute_only_single_line(client_code, fact_code, line_no, batch_no, sku_code, sku_name, upper_threshold, lower_threshold, weight_config, api_base_url):

    queue_lock = threading.Lock()
    total_remaining_time = weight_config['time_duration']
    tick = weight_config['tick']
    error_percentage = weight_config['error_percentage']

    thread_no = 1

    while total_remaining_time > 0:
        current_cycle_duration = min(60, total_remaining_time)

        prod_msg = f"[ EXECUTION - Line {line_no} | Thread_Number {thread_no}] Online -> Product: {sku_name} ({sku_code}) | Limits: [{lower_threshold}g - {upper_threshold}g] | Cycle: {current_cycle_duration}s "
        logging.info(prod_msg)
        exec_logger.info(prod_msg)

        log_queue = deque()
        api_queue = deque()
        weight_queue = deque()
        stop_event = threading.Event()

        checkweigher_thread = threading.Thread(
            target=checkweigher_machine,
            args=(client_code, sku_code, sku_name, fact_code, line_no, batch_no,
                  upper_threshold, lower_threshold, current_cycle_duration, tick, 
                  log_queue, api_queue, weight_queue, queue_lock, stop_event, error_percentage)
        )
        logger_thread = threading.Thread(target=write_to_logger, args=(log_queue, queue_lock, stop_event), daemon=False)
        db_insert_thread = threading.Thread(target=write_to_db, args=(api_queue, queue_lock, stop_event, api_base_url), daemon=False)

        checkweigher_thread.start()
        logger_thread.start()
        db_insert_thread.start()

        checkweigher_thread.join()
        
        stop_event.set()
        logger_thread.join()
        db_insert_thread.join()
        
        total_remaining_time -= current_cycle_duration

    stop_msg = f"[ STOPPED - Line {line_no}] execution finished ."
    exec_logger.info(stop_msg)


def run_single_line_pipeline(client_code, fact_code, line_no, batch_no, product_catalog, base_weight_config, api_base_url,thread_no):
    queue_lock = threading.Lock()
    total_remaining_time = base_weight_config['time_duration']
    tick = base_weight_config['tick']
    error_percentage = base_weight_config['error_percentage']

    bad_mess = ["unknown column", "sql syntax", "mysql error"]
    while total_remaining_time > 0:
        current_cycle_duration = min(60, total_remaining_time)
        chosen_product = random.choice(product_catalog)


        if isinstance(chosen_product, dict):
            sku_code = chosen_product.get("sku_code")
            sku_name = chosen_product.get("sku_name")
            
            thmax_val = chosen_product.get("thmax") or chosen_product.get("upper_threshold_limit")
            thmin_val = chosen_product.get("thmin") or chosen_product.get("lower_threshold_limit")

            if thmax_val is not None and float(thmax_val) > 0:
                upper_threshold_limit = float(thmax_val)
            if thmin_val is not None and float(thmin_val) > 0:
                lower_threshold_limit = float(thmin_val)

        if not sku_code or not sku_name or upper_threshold_limit is None or lower_threshold_limit is None:
            err_msg = f"[CRITICAL ERROR - Line {line_no}] Pulled product catalog item is missing crucial structure keys. Aborting thread execution."
            logging.critical(err_msg)
            break

        sku_code_str = str(sku_code).lower()
        is_corrupt = any(keyword in sku_code_str for keyword in bad_mess)

        if is_corrupt or len(str(sku_code)) > 15:
            err_msg = f"[CRITICAL ERROR - Line {line_no}] Detected corrupted SQL string in sku_code."
            logging.critical(err_msg)
            break

        prod_msg = f"[ PRODUCT CHANGE - Line {line_no} | Thread Number {thread_no}] Online -> Product: {sku_name} ({sku_code}) | Limits: [{lower_threshold_limit}g - {upper_threshold_limit}g] | Cycle: {current_cycle_duration}s remaining"
        logging.info(prod_msg)
        exec_logger.info(prod_msg)

        log_queue = deque()
        api_queue = deque()
        weight_queue = deque()
        stop_event = threading.Event()

        checkweigher_thread = threading.Thread(
            target=checkweigher_machine,
            args=(client_code, sku_code, sku_name, fact_code, line_no, batch_no,
                  upper_threshold_limit, lower_threshold_limit, current_cycle_duration, tick, 
                  log_queue, api_queue, weight_queue, queue_lock, stop_event, error_percentage)
        )
        logger_thread = threading.Thread(target=write_to_logger, args=(log_queue, queue_lock, stop_event), daemon=False)
        db_insert_thread = threading.Thread(target=write_to_db, args=(api_queue, queue_lock, stop_event, api_base_url), daemon=False)

        checkweigher_thread.start()
        logger_thread.start()
        db_insert_thread.start()

        checkweigher_thread.join()
        
        stop_event.set()
        logger_thread.join()
        db_insert_thread.join()
        
        total_remaining_time -= current_cycle_duration

    stop_msg = f"[ STOPPED - Line {line_no}] thread finished operations."
    exec_logger.info(stop_msg)


def start_streaming(api_config_file, product_config_file):

    config = configparser.ConfigParser()
    config.read(product_config_file)

    client_code = int(config['CheckweigherDetails']['ClientCode'])
    fact_code = config['CheckweigherDetails']['FactCode']

    weight_config = {
        'time_duration': int(config['WeightConfig']['TimeDuration']),
        'tick': float(config['WeightConfig']['SleepTime']),
        'error_percentage': float(config['WeightConfig']['ErrorPercentage'])
    }

    api_config = configparser.ConfigParser()
    api_config.read(api_config_file)
    api_base_url = api_config['ApiHostUrl']['api_base_host']

    # --- CHECK IF CONFIG FILE IS SINGLE LINE  ---
    is_direct_run = 'LineNo' in config['CheckweigherDetails'] and 'SkuCode' in config['CheckweigherDetails']

    if is_direct_run:
        msg_direct = f"Detected Direct Run Configuration. Initiating dedicated single line pipeline execution without dynamic API fetching..."
        exec_logger.info(msg_direct)
        
        try:
            line_no = int(config['CheckweigherDetails']['LineNo'])
            batch_no = str(config['CheckweigherDetails']['BatchNo'])
            sku_code = str(config['CheckweigherDetails']['SkuCode'])
            sku_name = str(config['CheckweigherDetails']['SkuName'])
            
            upper_threshold = float(config['WeightConfig']['UpperThresholdLimit'])
            lower_threshold = float(config['WeightConfig']['LowerThresholdLimit'])
        except KeyError as e:
            err_msg = f"CRITICAL ERROR: Direct run configuration file is missing explicit keys: {e}"
            logging.error(err_msg)
            sys.exit(1)
            
        execute_only_single_line(
            client_code, fact_code, line_no, batch_no, sku_code, sku_name, 
            upper_threshold, lower_threshold, weight_config, api_base_url
        )
        return

    # --- FALLBACK TO API NETWORK FETCHING (FILE 1) ---
    msg_init = f"Connecting to Django API at {api_base_url} to pull live factory structures..."
    exec_logger.info(msg_init)

    try:
        api_params1 = {"client_code": client_code}
        api_params2 = {"client_code": client_code, "fact_code": fact_code}
        
        #sku_code , sku_name , thmax, thmin from api
        product_url = f"http://{api_base_url}/api/v1/get-sku_code-and-sku_name/" 
        product_response = requests.get(product_url, params=api_params1, timeout=5)
        product_response.raise_for_status() 
        product_catalog = product_response.json() 
        
        #batch_no, line_no from this api
        factory_url = f"http://{api_base_url}/api/v1/get-line_no-and-batch_no/" 
        factory_response = requests.get(factory_url, params=api_params2, timeout=5)
        factory_response.raise_for_status()
        factory_setup = factory_response.json() 
        
    except Exception as e:
        err_msg = f"CRITICAL ERROR: Failed to fetch startup configuration from API endpoint: {e}"
        logging.error(err_msg)
        sys.exit(1)

    if isinstance(product_catalog, dict):
        product_catalog = list(product_catalog.values())

    if not product_catalog or not isinstance(product_catalog, list):
        err_msg = "ERROR: Received empty or invalid product catalog data format from API."
        logging.error(err_msg)
        sys.exit(1)

    if not factory_setup:
        err_msg = "ERROR: No active production line configuration returned from API setup data."
        logging.error(err_msg)
        sys.exit(1)

    msg_spawn = f"Spawning factory network for Client: {client_code} | Factory: {fact_code} | Deploying production line threads..."
    exec_logger.info(msg_spawn)

    # if isinstance(factory_setup, dict):
    #     iterator = factory_setup.items()
    if isinstance(factory_setup, list):
        iterator = []
        for element in factory_setup:
            if isinstance(element, dict):
                iterator.append((element.get("line_no"), element.get("batch_no")))
            # elif isinstance(element, (list, tuple)) and len(element) >= 2:
            #     iterator.append((element[0], element[1]))
    else:
        err_msg = "ERROR: factory_setup data layout is unrecognizable."
        logging.error(err_msg)
        sys.exit(1)

    if not iterator:
        err_msg = "ERROR: Cleaned factory iterable configuration has zero elements."
        logging.error(err_msg)
        sys.exit(1)

    thread_no = 1
    active_threads = []
    for line_key, batch_val in iterator:
        if line_key is None or batch_val is None:
            break
            
        line_no = int(line_key)
        batch_no = str(batch_val)
        
        # except (ValueError, TypeError):
        #     continue
        
        t = threading.Thread(
            target=run_single_line_pipeline,
            args=(client_code, fact_code, line_no, batch_no, product_catalog, weight_config, api_base_url,thread_no),
            name=f"Pipeline-Line-{line_no}"
        )
        t.daemon = False 
        t.start()
        active_threads.append(t)
        thread_no += 1
        time.sleep(0.1)

    for t in active_threads:
        t.join()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        err_msg = "ERROR: Execution halted. Usage requires a configuration file argument: python main.py <config_file>"
        logging.critical(err_msg)
        sys.exit(1)

    base_name = sys.argv[1] 
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)

    possible_files = [
        os.path.join(root_dir, base_name),
        os.path.join(root_dir, base_name + ".ini"),
        os.path.join(root_dir, base_name + ".cfg"),
        os.path.join(current_dir, base_name),
        os.path.join(current_dir, base_name + ".ini"),
        os.path.join(current_dir, base_name + ".cfg"),
    ]

    config_file = None
    for f in possible_files:
        if os.path.exists(f):
            config_file = f
            break

    if not config_file:
        err_msg = f"ERROR: Configuration framework failed to start. No configuration file found matching target name '{base_name}'."
        logging.critical(err_msg)
        sys.exit(1)
        
    api_host_config = os.path.join(root_dir, "apiConfig.ini")
    start_streaming(api_config_file=api_host_config, product_config_file=config_file)