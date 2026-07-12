import time, random, datetime

class ProductDetails():
    def __init__(self):
        self.ClientCode = None
        self.PCode = None
        self.PName = None
        self.FactCode = None
        self.LineNo = None
        self.BatchNo = None
        self.UpperThreshold = None
        self.LowerThreshold = None
        self.Weight = None
        self.Status = None
        self.ProductionTime = None

    def to_dict(self):
        return {
            "client_code": self.ClientCode,
            "sku_code": self.PCode,
            "sku_name": self.PName,
            "fact_code": self.FactCode,
            "line_no": self.LineNo,
            "batch_no": self.BatchNo,
            "upper_threshold": self.UpperThreshold,
            "lower_threshold": self.LowerThreshold,
            "weight": self.Weight,
            "product_status": self.Status,
            "production_time": self.ProductionTime
        }


def weight_gen(upper, lower, weight_queue, queue_lock, error_percentage):

    bucket = []

    total_samples = 10

    error_count = round((error_percentage / 100) * total_samples)

    if error_count % 2 != 0:
        error_count -= 1

    error_count = max(0, min(error_count, total_samples))

    normal_count = total_samples - error_count

    bucket.extend([round(random.uniform(lower, upper), 2) for _ in range(normal_count)])

    underweight_count = error_count // 2
    overweight_count = error_count // 2

    bucket.extend([
        round(random.uniform(lower - 5, lower - 0.01), 2)
        for _ in range(underweight_count)
    ])

    # Generate overweight values
    bucket.extend([
        round(random.uniform(upper + 0.01, upper + 5), 2)
        for _ in range(overweight_count)
    ])

    # lower_outlier = round(random.uniform(lower - 5, lower - 0.01), 2)
    # bucket.append(lower_outlier)
    # random.shuffle(bucket)

    # upper_outlier = round(random.uniform(upper + 0.01, upper + 5), 2)
    # bucket.append(upper_outlier)
    random.shuffle(bucket)

    # for val in bucket:
    #     with queue_lock:
    #         if bucket:
    #             weight_queue.append(val)

    with queue_lock:
        weight_queue.extend(bucket)

    bucket.clear()


def checkweigher_machine(client_code, sku_code, sku_name, fact_code, line_no, batch_no, upper_threshold_limit, lower_threshold_limit, time_duration, tick, log_queue, api_queue, weight_queue, queue_lock, stop_event, error_percentage):
    start_time = time.time()    

    print(f"Starting weight generation for {time_duration} seconds and error outlier would be {error_percentage} percentage.")

    while (time.time() - start_time) < time_duration:
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

        product = ProductDetails()

        product.ClientCode = client_code
        product.PCode = sku_code
        product.PName = sku_name
        product.FactCode = fact_code
        product.LineNo = line_no
        product.BatchNo = batch_no
        product.UpperThreshold = upper_threshold_limit
        product.LowerThreshold = lower_threshold_limit
        product.ProductionTime = formatted_current_time

        if len(weight_queue) == 0:
            weight_gen(product.UpperThreshold, product.LowerThreshold, weight_queue, queue_lock, error_percentage)

        with queue_lock:
            if weight_queue:
                product.Weight = weight_queue.pop()
            else:
                continue
        if product.Weight > product.LowerThreshold and product.Weight < product.UpperThreshold:
            product.Status = 'pass'
        elif product.Weight < product.LowerThreshold:
            product.Status = 'underweight'
        else:
            product.Status = 'overweight'

        with queue_lock:
            log_queue.appendleft(product)
            api_queue.appendleft(product.to_dict())

        time.sleep(tick)
    
    stop_event.set()
    print(f"{time_duration} seconds done. Stopping generation")