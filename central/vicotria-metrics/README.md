# Victoria Metrics
The reason this container exists is to separate the logic of reading data using MetricsQL using direct HTTP calls with a return of data 

## Data Flow
Once the data got through the mqtt broker and the EGDE compute that publishes it on Kafka, the Telegraf will be watching
all publications on Kafka. These subscripted messages have their own JSON structure. In Telegraf it gets translated into 
ILP. Those ILP lines are the ones actually stored in VictoriaMetrics. 

## Scope
The scope here is to cover the process from reading Kafka messages up to reading the data from DB.

## Kafka Message
Kafka messages value has format is as follows:

```json
{
  "measurement": <physical-value-type>,
  "tags": {
    "hotel_id": <hotel-id>,
    "room": <room-number>,
    "sensor": <uuid>,
  },
  "fields": {
    <sensor-data-type>: <value>,
    <sensor-data-type>: <value>...
  },
  "timestamp": 1695800105
}
```

## ILP
temperature,hotel_id=DUB-Grand,room=621,sensor=8bce3cf7-4f63-4d20-b2b4-bf5b88e777199 t=21,status=0 1695986400123000000

# Querying Victoria Metrics
Victoria Metrics has a built-in Prometheus-compatible query API. You can use this API to query the stored metrics data.

## Direct Connection to Victoria Metrics
You can connect directly to the Victoria Metrics instance using its HTTP API. The default port for Victoria Metrics is `8428`.

## Using a created API Gateway 
You can connect to vm-api to retrieve most often used metrics. The base URL is as follows:

Current routes:
- `/api/v1/metrics/temperature` - Get temperature metrics
- `/api/v1/metrics/light` - Get light status

Example using `curl` to get temperature metrics:

### Example Curl Command
```bash
curl -X GET "http://vm-api:8080/api/v1/metrics/temperature?hotel_id=DUB-Grand&room=621&start=1695892800
```

This command retrieves temperature metrics for room 621 in the DUB-Grand hotel starting from the specified timestamp.

The api just connects to vm and runs the following query:
```
QUERY='avg(avg_over_time(temperature{hotel_id="DUB-Grand",room="621"}[60s]))'

# Curl against VictoriaMetrics HTTP API
curl --get 'http://victoria-metrics:8428/api/v1/query' \
  --data-urlencode "query=${QUERY}"
```

### Example Response
```json
{
  "status": "success",
  "data": {
    "result": [
      {
        "metadata": {temperature": "temperature", "hotel_id": "DUB-Grand", "room": "621"},
        "value": [1695986400, "21"]
      }
    ]
  }
}
```

### API health check
To check if the API is running, you can use the following curl command:
```bash
curl -X GET "http://vm-api:8080/health"
```
This should return a simple status message indicating that the API is operational. It performs an empty connection to 
Victoria Metrics to ensure connectivity.
```json
{"status": "ok"}
```
