from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
from newsapi import NewsApiClient
import os
from dice_roller import DiceRoller

load_dotenv()

mcp = FastMCP("mcp-server")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for information about the given query"""
    search_results = client.get_search_context(query=query)
    return search_results

@mcp.tool()
def roll_dice(notation: str, num_rolls: int = 1) -> str:
    """Roll the dice with the given notation"""
    roller = DiceRoller(notation, num_rolls)
    return str(roller)

@mcp.tool()
def get_marketing_news(company: str = None, category: str = "business", num_articles: int = 5) -> str:
    """
    Get the latest marketing and business news from companies like ZoomInfo, 6sense, and other marketing tech companies.
    
    Args:
        company: Specific company to search for (e.g., 'ZoomInfo', '6sense', 'HubSpot', 'Salesforce')
        category: News category (default: 'business', options: 'business', 'technology', 'general')
        num_articles: Number of articles to return (default: 5, max: 100)
    """
    try:
        # Marketing tech companies and related keywords
        marketing_companies = [
            'ZoomInfo', '6sense', 'HubSpot', 'Salesforce', 'Marketo', 'Pardot', 
            'Adobe', 'Oracle', 'Microsoft', 'Google', 'Facebook', 'LinkedIn',
            'Mailchimp', 'Constant Contact', 'SendGrid', 'Twilio', 'Segment',
            'Amplitude', 'Mixpanel', 'Tableau', 'Looker', 'Snowflake'
        ]
        
        # Build search query
        if company:
            query = f"{company} marketing OR {company} sales OR {company} business"
        else:
            query = "marketing technology OR martech OR sales technology OR business intelligence"
        
        # Get news articles
        articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            page_size=min(num_articles, 100)
        )
        
        if articles['status'] == 'ok' and articles['totalResults'] > 0:
            result = f"📈 Marketing News ({len(articles['articles'])} articles found):\n\n"
            
            for i, article in enumerate(articles['articles'][:num_articles], 1):
                title = article['title']
                description = article['description'] or "No description available"
                source = article['source']['name']
                url = article['url']
                published = article['publishedAt'][:10]  # Just the date
                
                result += f"{i}. **{title}**\n"
                result += f"   📰 Source: {source}\n"
                result += f"   📅 Published: {published}\n"
                result += f"   📝 Description: {description}\n"
                result += f"   🔗 URL: {url}\n\n"
            
            return result
        else:
            return f"❌ No marketing news found for query: {query}"
            
    except Exception as e:
        return f"❌ Error fetching marketing news: {str(e)}"

@mcp.tool()
def get_company_news(company: str, num_articles: int = 3) -> str:
    """
    Get specific news about a particular company (e.g., ZoomInfo, 6sense, etc.)
    
    Args:
        company: Company name to search for
        num_articles: Number of articles to return (default: 3)
    """
    try:
        articles = newsapi.get_everything(
            q=f"{company}",
            language='en',
            sort_by='publishedAt',
            page_size=min(num_articles, 100)
        )
        
        if articles['status'] == 'ok' and articles['totalResults'] > 0:
            result = f"🏢 {company} News ({len(articles['articles'])} articles found):\n\n"
            
            for i, article in enumerate(articles['articles'][:num_articles], 1):
                title = article['title']
                description = article['description'] or "No description available"
                source = article['source']['name']
                url = article['url']
                published = article['publishedAt'][:10]
                
                result += f"{i}. **{title}**\n"
                result += f"   📰 Source: {source}\n"
                result += f"   📅 Published: {published}\n"
                result += f"   📝 Description: {description}\n"
                result += f"   🔗 URL: {url}\n\n"
            
            return result
        else:
            return f"❌ No news found for company: {company}"
            
    except Exception as e:
        return f"❌ Error fetching company news: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")