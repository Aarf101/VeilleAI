from watcher.agents.filter import SmartFilter
config = {'feeds_weight': {'https://www.artificialintelligence-news.com/feed/': 0.1}}
flt = SmartFilter(['Artificial Intelligence'], threshold=0.5, config=config)

article = {
    'title': 'Artificial Intelligence is taking over the world',
    'summary': 'AI is everywhere.',
    'feed_url': 'https://www.artificialintelligence-news.com/feed/'
}

res, score, method = flt.match_article_to_topic(article, 'Artificial Intelligence')
print(f"Passed: {res}, Score: {score}, Method: {method}")
