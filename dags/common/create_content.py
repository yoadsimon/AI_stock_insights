import yfinance as yf
import datetime
import asyncio
import logging
from tqdm import tqdm

from common.utils.consts import MARKET_TIME_ZONE
from common.utils.open_ai import generate_stock_opening_analysis, summarize_with_open_ai
from common.utils.stock_market_time import StockMarketTime
from common.utils.utils import get_text_by_url, save_to_s3, read_from_s3


def save_file(data: str, stock_symbol: str, now_date: str,
              dag_name: str = "daily_stock_analysis",
              prefix: str = 'data') -> None:
    file_name = f"{stock_symbol}/{dag_name}/{prefix}/{now_date}"
    save_to_s3(file_type="txt", file_name=file_name, data=data)


def read_file(stock_symbol: str, now_date: str,
              dag_name: str = "daily_stock_analysis",
              prefix: str = 'data') -> str:
    file_name = f"{stock_symbol}/{dag_name}/{prefix}/{now_date}"
    return read_from_s3(file_name)


def create_content(use_temp_file=False,
                   stock_symbol='NVDA',
                   company_name='NVIDIA Corporation',
                   stock_market_time=None,
                   ) -> str:
    now_date = stock_market_time.now.strftime("%Y-%m-%d")
    stock_info = read_file(stock_symbol=stock_symbol,
                           now_date=now_date) if use_temp_file else None

    if not stock_info:
        stock_info = get_stock_data(stock_symbol, company_name, stock_market_time)
        save_file(data=stock_info,
                  stock_symbol=stock_symbol,
                  now_date=now_date)
    print("Generating stock opening analysis...")
    result = generate_stock_opening_analysis(stock_info, company_name, stock_symbol)
    save_file(data=result,
              stock_symbol=stock_symbol,
              now_date=now_date,
              prefix='generated_result')
    return result


def get_stock_data(stock_symbol: str, company_name: str, stock_market_time: StockMarketTime) -> str:
    print("Getting stock data...")
    price_data = get_price_data(stock_symbol, stock_market_time)
    print("Getting news data...")
    news_data = get_news_data(company_name, stock_symbol, stock_market_time)
    return f"Stock Data for {company_name} ({stock_symbol}):\n\n" \
           f"Price Data:\n{price_data}\n\n" \
           f"News Data:\n{news_data}"


def get_price_data(stock_symbol: str, stock_market_time: StockMarketTime) -> str:
    stock = yf.Ticker(stock_symbol)
    start = stock_market_time.last_time_close
    end = stock_market_time.next_time_open
    stock_data = stock.history(period="5d", interval="1m", prepost=True)
    stock_data = stock_data[(stock_data.index >= start) & (stock_data.index <= end)]
    # stock_data.to_csv(f"temp/{stock_symbol}_data.csv")
    # check if data is empty
    if stock_data.empty:
        if not stock_market_time.is_mock:
            raise Exception("No stock data available for the specified time period.")
        return (
            f"Previous Close (Yesterday): 142.01\n"
            f"Open Price (Today): 133.91\n"
        )
    previous_close = stock_data.iloc[0]['Open']
    open_price = stock_data.iloc[-1]['Open']

    return (
        f"Previous Close (Yesterday): {previous_close}\n"
        f"Open Price (Today): {open_price}\n"
    )


def get_news_data(company_name: str, stock_symbol: str, stock_market_time: StockMarketTime) -> str:
    stock = yf.Ticker(stock_symbol)
    news = stock.news
    relevant_news = []
    urls = set()
    for news_item in tqdm(news):
        published_timestamp = news_item['providerPublishTime']
        published_time = datetime.datetime.fromtimestamp(published_timestamp, MARKET_TIME_ZONE)
        if not stock_market_time.is_mock and not (
                stock_market_time.last_time_close < published_time < stock_market_time.next_time_open):
            continue
        url = news_item.get('link')
        if not url:
            continue
        relevant_news.append(news_item)
        urls.add(url)
    print(f"Number of relevant news items: {len(relevant_news)}")
    if not relevant_news:
        return (f"No relevant news found for {company_name} "
                f"between {stock_market_time.last_time_close} and "
                f"{stock_market_time.next_time_open}.")

    text_by_link = asyncio.run(get_text_by_url(urls))
    news_data = ""
    # TODO - put it in a thread
    for news_item in tqdm(relevant_news):
        link = news_item['link']
        text = text_by_link.get(link)
        if not text:
            continue

        published_timestamp = news_item['providerPublishTime']
        published_time = datetime.datetime.fromtimestamp(published_timestamp, MARKET_TIME_ZONE)
        summary = summarize_with_open_ai(text, link, company_name, stock_symbol)
        if not summary:
            continue

        news_data += (f"Headline: {news_item['title'].strip()}\n"
                      f"Date: {published_time}\n"
                      f"Summary: {summary.strip()}\n\n")

    return news_data

# if __name__ == '__main__':
#     save_stock_info(stock_info="test",
#                     stock_symbol="NVDA",
#                     now_date="2021-09-01")
