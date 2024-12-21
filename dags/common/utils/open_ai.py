from airflow.hooks.base_hook import BaseHook
from openai import OpenAI

from common.inputs.video_map import VIDEO_DESCRIPTION_MAP
from common.utils.consts import DISCLAIMER_VIDEO_TEXT
from common.utils.utils import fix_video_name


class OpenAIClient():
    def __init__(self, conn_id='openai_default'):
        conn = BaseHook.get_connection(conn_id)
        extra = conn.extra_dejson
        self.client = OpenAI(
            organization=extra.get('organization'),
            project=extra.get('project'),
            api_key=extra.get('api_key')
        )

    def generate_text(self, prompt, model="gpt-4o-mini"):
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
            )
            result = response.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}")
            result = None
        return result


def check_if_article_relevant(text, link, company_name, stock_symbol, client) -> bool:
    prompt = (
        "You are a financial analyst specializing in evaluating news articles for their potential impact on a company's stock price.\n"
        "Analyze the following article and determine whether it is relevant to the future stock price movement of the specified company.\n"
        "Consider factors such as financial performance, market conditions, legal issues, management changes, or other significant events that could influence the stock price.\n"
        "Respond with 'True' if the article is relevant, or 'False' if it is not.\n"
        "Your response should be only 'True' or 'False'.\n"
        f"Company Name: {company_name}\n"
        f"Stock Symbol: {stock_symbol}\n"
        f"Article Link: {link}\n"
        f"Article Text: {text}"
    )
    response = client.generate_text(prompt)
    try:
        return response.strip().lower() == 'true'
    except Exception as e:
        print(f"Error: {e}")
        return False


def summarize_with_open_ai(text, link, company_name, stock_symbol):
    client = OpenAIClient()
    is_article_relevant = check_if_article_relevant(text, link, company_name, stock_symbol, client)
    if not is_article_relevant:
        return None
    prompt = (
        f"You are a financial analyst with expertise in assessing news impact on stock prices in the immediate term.\n"
        f"Please perform the following tasks:\n"
        f"1. **Summarize** the following news article related to {company_name} ({stock_symbol}) in 2-3 sentences.\n"
        f"2. **Evaluate** the likely impact of this news on the company's stock price for the next trading day. Indicate whether the impact is **positive**, **negative**, or **neutral**.\n"
        f"3. **Explain** your reasoning in 1-2 sentences.\n"
        f"Provide your response in a clear and organized manner, numbering each part accordingly.\n\n"
        f"Article Link: {link}\n\n"
        f"Article Text:\n{text}\n"
    )
    summary = client.generate_text(prompt)
    return summary


def generate_stock_opening_analysis(text, company_name, stock_symbol):
    client = OpenAIClient()
    prompt = (
        f"You are a seasoned financial analyst and market commentator.\n"
        f"Based on the latest news and developments related to {company_name} ({stock_symbol}), "
        f"provide a concise and insightful analysis of how the stock is likely to perform when the market opens today.\n"
        f"Your explanation should be professional, use clear language, and be suitable for an audio briefing to investors.\n\n"
        f"Latest News Summary:\n{text}\n\n"
        f"Your analysis should include:\n"
        f"1. A prediction on whether the stock will go **up** or **down** at market open, and why.\n"
        f"2. An estimated percentage of the expected price movement.\n"
        f"3. Key factors from the news that support your prediction.\n"
        f"Please present your analysis in a single, well-structured paragraph."
    )
    results = client.generate_text(prompt)
    return results


def match_text_to_video(text, last_video_name) -> str:
    client = OpenAIClient()

    video_description_map = VIDEO_DESCRIPTION_MAP.copy()
    if last_video_name:
        del video_description_map[last_video_name]

    prompt = f"""
    You are given a mapping of video descriptions and their corresponding video file names.
    Here is the video description map: {video_description_map}

    Your task is to analyze the following sentence and find the video whose description from the description map holds the most relevance.

    Sentence: "{text}"

    Return ONLY the name of the video file that best matches the sentence.
    """

    response = client.generate_text(prompt)
    response = fix_video_name(response)
    return response


def create_description_youtube_video(text, company_name, stock_symbol, now):
    print(f"creating description...")
    client = OpenAIClient()
    prompt = (
        f"You are a financial analyst creating a YouTube video description for an AI-generated stock analysis of {company_name} ({stock_symbol}). "
        f"Your task is to write a compelling and engaging description that highlights the key points of the analysis and entices viewers to watch the video. "
        f"The description should be concise, informative, and provide a preview of the valuable insights shared in the video.\n\n"
        f"Title: {company_name} - {stock_symbol} AI Stock Analysis - {now.strftime('%Y-%m-%d')}\n\n"
        f"Analysis Summary: \n{text}\n{DISCLAIMER_VIDEO_TEXT}\n\n"
        f"Please include a disclaimer stating that the video is AI-generated and should not be used for real investment decisions, but only for learning purposes."
    )
    results = client.generate_text(prompt)
    final_description = results + "\n\n" + f"Text of the video:\n {text}"
    return final_description
