# Never Miss That Deal Agian
## AWS Lambda

A #lambda function scraps, transforms the data, puts item in #DynamoDB, and invokes the another lambda function, emailer, to send a notification.

A layer is added to import #requests and #BeautifulSoup.

It runs once a minute and is triggered by a #CloudWatch event.

From input to output, nothing needs to be local on this occasion.
