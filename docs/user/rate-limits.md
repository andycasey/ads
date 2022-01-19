# Rate limits and throttling 

## Rate limits

The number of API requests you can make to ADS per day is limited. There is a good reason for this: to prevent the system from collapsing. Every time an API call is made with the `ads` package, it tracks the number of API calls you have remaining, and how long until that counter is reset. The `ads` package tries its best to keep track of these for the different ADS services, because the API limits for each service are slightly different. If you get to the stage where you are worrying about rate limits, you are among the 1%!

### Check your limits

There's no specific API end point to check your current limits, but this information is returned in the response header for most API end points. That means we just need to make a single API call in order to know the current rate limits. 

In the example below you can see the executable Python code in the first tab, and the output in the second tab.

``````{tab} Python
```python
from ads import Document
from ads.client import RateLimits
from datetime import datetime

# Make any API call to the Apache Solr (search) service.
doc = Document.get()

# Check our current limits.
limits = RateLimits()

# If we want to print the limits, we can just use print.
print(limits)

# Or we can access details about individual service limits.
solr_limits = RateLimits.get_rate_limits("solr")

# Calculate how long until our limit resets.
dt = datetime.utcnow() - datetime.fromtimestamp(solr_limits["reset"])
hrs, mins = (dt.seconds // 3600, (dt.seconds // 60) % 60)
print(f"There are {hrs} hour(s) and {mins} minute(s) until reset")
```
``````
``````{tab} Output
```bash
{
  "solr": {
    "limit": 5000,
    "remaining": 4980,
    "reset": 1642568331
  }
}
There are 9 hour(s) and 59 minute(s) until reset
```
``````

## Throttling

In Version 1.0 of the `ads` package you can search for documents using asynchronous coroutines, without having to write (nearly) any extra code. For ADS power-users, that creates a risk of accidentally overloading the ADS servers. For this reason, there are in-built throttling mechanisms to prevent excess load on the ADS servers.

In previous versions of the `ads` package, a search with many results would have each page of results fetched in serial. For example, a search with 1,000 results with 200 results being sent per page would need five API queries, one for each page. The second query would not start until after the first query is finished, and so on. 

Here is an example of how an asynchronous search might be executed by the `ads` package:

1. A query is supplied without any limit on the number of records to return.
2. The `ads` package initiates the query for the first page of results. When the first page is returned, the header information tells us how many records there are in total.
3. Knowing how many records are returned per page and the total number of records, we initiate simultaneous queries for all remaining pages.
4. Order the results from the queries in the right way so the user gets the same behaviour in synchronous and asynchronous mode.

At Step 3 it is possible for us to start an absurd number of simultaneous requests. In this case, absurd might be 100, or 10 million. For this reason, every API request that is sent from the `ads` package uses a low-level throttler to limit the number of simultaneous requests. If the search function wants to create 10 million requests, then it will pause (in another asynchronous loop) until the maximum number of asynchronous requests is not reached. By default this limit is set to ten simultaneous requests.

**See also:**
- [Using asynchronous coroutines](../tutorials/async)
