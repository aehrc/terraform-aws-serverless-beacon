import os
import time
import random
import re
import json

import requests
import numpy as np


API_URL = os.environ['SBEACON_API_URL']
random.seed(42)
pattern = re.compile(f'^\\w[^:]+:.+$')


def timeit(func, /, desc):
    def dec(*args, **kwargs):
        start = time.time()
        res =  func(*args, **kwargs)
        end = time.time()
        print(f'{desc:40} - {end-start:7.3f}s')
        return res
    return dec
    
    
def extract_terms(array):
    for item in array:
        if type(item) == dict:
            for key, value in item.items():
                if type(value) == str:
                    if key == "id" and pattern.match(value):
                        yield value
                if type(value) == dict:
                    yield from extract_terms([value])
                elif type(value) == list:
                    yield from extract_terms(value)
        if type(item) == str:
            continue
        elif type(item) == list:
            yield from extract_terms(item)
            

def compute_times(url, method, /, body, params, reps=1):
    times = []
    for _ in range(reps):
        start = time.time()
        if method == 'post':
            response = timeit(requests.post)(url=url, json=body)
        if method == 'get':
            response = requests.get(url=url, params=params)
        end = time.time()
        times.append(start - end)
    assert response
    # to numpy skipping the potential cold run
    times = np.array(times[1:])
    return times
    

# test for individuals
body = {
    "meta": {
        "apiVersion": "v2.0"
    },
    "query": {
        "requestedGranularity": "record",
        "filters": [

        ],
        "pagination": {
            "limit": 100,
            "skip": 0
        }
    }
}

print('Selecting a test case')

# datasets
url = f'{API_URL}/datasets'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
response = response['response']['resultSets'][0]['results']
chosen = random.choice(response)
dataset_id = chosen['id']
dataset_terms = list(extract_terms([chosen]))

# cohorts
cohort_id = dataset_id
url = f'{API_URL}/cohorts/{cohort_id}'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
response = response['response']['resultSets'][0]['results'][0]
cohort_terms = list(extract_terms([response]))

# individuals
url = f'{API_URL}/datasets/{dataset_id}/individuals'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
response = response['response']['resultSets'][0]['results']
chosen = random.choice(response)
individual_id = chosen['id']
individual_terms = list(extract_terms([chosen]))

# biosamples
url = f'{API_URL}/individuals/{individual_id}/biosamples'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
response = response['response']['resultSets'][0]['results']
chosen = random.choice(response)
biosample_id = chosen['id']
biosample_terms = list(extract_terms([chosen]))

# runs
url = f'{API_URL}/biosamples/{biosample_id}/runs'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
response = response['response']['resultSets'][0]['results']
chosen = random.choice(response)
run_id = chosen['id']
run_terms = list(extract_terms([chosen]))

# complex query terms
query_terms = [
    {
        "id": random.choice(dataset_terms),
        "scope": "datasets"
    },
    {
        "id": random.choice(individual_terms),
        "scope": "individuals"
    },
    {
        "id": random.choice(biosample_terms),
        "scope": "biosamples"
    },
    {
        "id": random.choice(run_terms),
        "scope": "runs"
    },
    {
        "id": random.choice(cohort_terms),
        "scope": "cohorts"
    }
]

body['query']['filters'] = query_terms

print('Running complex metadata queries')
print(json.dumps(body, indent=4))

# datasets
url = f'{API_URL}/datasets'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()

# cohorts
url = f'{API_URL}/cohorts'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()

# individuals
url = f'{API_URL}/individuals'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()

# biosamples
url = f'{API_URL}/biosamples'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()

# runs
url = f'{API_URL}/runs'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()

# analyses
url = f'{API_URL}/analyses'
response = timeit(requests.post, url.replace(API_URL, ''))(url, json=body).json()
