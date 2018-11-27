# git-analysis
Dump git data into elasticsearch for analysis

To load the mapping run
curl -XPUT 'http://localhost:9200/git' -H 'Content-Type: application/json' -d @mapping.json

