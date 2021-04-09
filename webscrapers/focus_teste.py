from webscrapers import FocusIPCA

focus = FocusIPCA(r'/Users/gustavoamarante/Desktop/chromedriver')

df = focus.scrape('2018-01-01', '2021-12-31')

print(df)

