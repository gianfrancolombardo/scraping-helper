# Scraping Helper
Helper class for scraping web with random proxies and user agents

## Usage

```python
if __name__ == "__main__":

    scrap = Scraping()

    url = 'https://thecodinglove.com/'
    page = scrap.get_page(url)               
    for item in page.find_all("h1", class_='index-blog-post-title'):
        print(item.text)
```