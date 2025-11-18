"""
Router for news updates.

Handles fetching news articles from News API and saving them to the database.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging

from ...database import DatabaseService
from ...news_fetcher import NewsFetcher
from ..dependencies import get_db
from ..schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["News Updates"],
)


# =============================================================================
# POST /api/stocks/{symbol}/update-news - Fetch and save news for a stock
# =============================================================================

@router.post(
    "/stocks/{symbol}/update-news",
    response_model=dict,
    summary="Fetch and save news articles from News API",
    description="Fetches the latest news articles for a stock from News API and saves them to database.",
    responses={
        200: {
            "description": "News fetched and saved successfully"
        },
        404: {
            "description": "Stock not found",
            "model": ErrorResponse
        },
        503: {
            "description": "News API error or timeout",
            "model": ErrorResponse
        }
    }
)
async def update_stock_news(
    symbol: str,
    limit: int = Query(
        5,
        ge=1,
        le=20,
        description="Number of news articles to fetch (1-20, default: 5)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Fetch and save news articles for a stock.

    This endpoint:
    1. Verifies the stock exists in the database
    2. Fetches latest news articles from News API
    3. Saves each article to the database
    4. Returns summary of saved articles

    **Note**: Requires NEWS_API_KEY in environment variables.

    Parameters:
    - **symbol**: Stock symbol (e.g., AAPL, TSLA)
    - **limit**: Number of articles to fetch (default: 5, max: 20)

    Returns:
    - **message**: Success message
    - **symbol**: Stock symbol
    - **company_name**: Company name used for search
    - **total_fetched**: Number of articles fetched from API
    - **total_saved**: Number of articles saved to database
    - **articles**: List of saved articles

    Errors:
    - **404**: Stock not found in database
    - **503**: News API error or timeout
    """
    # Verify stock exists
    stock = db.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol.upper()}' not found"
        )

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Fetch news from News API using company name
    try:
        articles = fetcher.get_articles(stock.company_name, limit=limit)
        logger.info(f"Fetched {len(articles)} articles for {symbol} from News API")
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch news from News API: {str(e)}"
        )

    # Save articles to database
    saved_articles = []
    saved_count = 0
    skipped_count = 0

    for article in articles:
        try:
            # Extract article data
            title = article.get("title")
            description = article.get("description")
            url = article.get("url")
            image_url = article.get("urlToImage")
            source = article.get("source", {}).get("name")
            published_at_str = article.get("publishedAt")

            # Skip if no title
            if not title:
                continue

            # Check if article already exists (duplicate detection by URL)
            if url and db.has_news_article_by_url(symbol, url):
                logger.info(f"Skipping duplicate article for {symbol}: {url}")
                skipped_count += 1
                continue

            # Parse published_at date
            from datetime import datetime
            published_at = None
            if published_at_str:
                try:
                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                except:
                    pass

            # Save to database
            saved_article = db.save_news_article(
                symbol=symbol,
                title=title,
                description=description,
                url=url,
                image_url=image_url,
                source=source,
                published_at=published_at
            )

            if saved_article:
                saved_articles.append({
                    "id": saved_article.id,
                    "title": saved_article.title,
                    "source": saved_article.source,
                    "url": saved_article.url,
                    "published_at": saved_article.published_at.isoformat() if saved_article.published_at else None,
                    "fetched_at": saved_article.fetched_at.isoformat()
                })
                saved_count += 1

        except Exception as e:
            logger.error(f"Error saving article for {symbol}: {str(e)}")
            # Continue with next article
            continue

    logger.info(f"Saved {saved_count} of {len(articles)} articles for {symbol} (skipped {skipped_count} duplicates)")

    return {
        "message": f"News updated successfully for {symbol}",
        "symbol": symbol.upper(),
        "company_name": stock.company_name,
        "total_fetched": len(articles),
        "total_saved": saved_count,
        "total_skipped": skipped_count,
        "articles": saved_articles
    }


# =============================================================================
# POST /api/stocks/update-all-news - Fetch news for all active stocks
# =============================================================================

@router.post(
    "/stocks/update-all-news",
    response_model=dict,
    summary="Fetch news for all active stocks",
    description="Fetches latest news articles for all active stocks from News API.",
    responses={
        200: {
            "description": "News fetched for all stocks"
        }
    }
)
async def update_all_stock_news(
    limit: int = Query(
        5,
        ge=1,
        le=20,
        description="Number of articles per stock (1-20, default: 5)"
    ),
    db: DatabaseService = Depends(get_db)
):
    """
    Fetch news for all active stocks.

    This endpoint:
    1. Fetches all active stocks from database
    2. Fetches news for each stock from News API
    3. Saves articles to database
    4. Returns summary of updates

    **Note**: Be mindful of News API rate limits when updating many stocks.

    Parameters:
    - **limit**: Number of articles per stock (default: 5, max: 20)

    Returns:
    - **message**: Summary message
    - **total_stocks**: Total number of stocks in database
    - **active_stocks**: Number of active stocks
    - **updated**: Number of stocks successfully updated
    - **failed**: Number of stocks that failed
    - **total_articles_saved**: Total articles saved across all stocks
    - **results**: List of per-stock results
    """
    # Get all active stocks
    active_stocks = db.get_all_stocks(only_active=True)
    total_stocks = len(db.get_all_stocks(only_active=False))

    if not active_stocks:
        return {
            "message": "No active stocks to update",
            "total_stocks": total_stocks,
            "active_stocks": 0,
            "updated": 0,
            "failed": 0,
            "total_articles_saved": 0,
            "results": []
        }

    # Initialize counters
    updated_count = 0
    failed_count = 0
    total_articles_saved = 0
    results = []

    # Initialize fetcher once
    fetcher = NewsFetcher()

    # Update each stock
    for stock in active_stocks:
        result = {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "success": False,
            "articles_fetched": 0,
            "articles_saved": 0,
            "articles_skipped": 0,
            "error": None
        }

        try:
            # Fetch news from News API
            articles = fetcher.get_articles(stock.company_name, limit=limit)
            result["articles_fetched"] = len(articles)

            # Save articles to database
            saved_count = 0
            skipped_count = 0
            for article in articles:
                try:
                    title = article.get("title")
                    if not title:
                        continue

                    description = article.get("description")
                    url = article.get("url")
                    image_url = article.get("urlToImage")
                    source = article.get("source", {}).get("name")
                    published_at_str = article.get("publishedAt")

                    # Check if article already exists (duplicate detection by URL)
                    if url and db.has_news_article_by_url(stock.symbol, url):
                        logger.info(f"Skipping duplicate article for {stock.symbol}: {url}")
                        skipped_count += 1
                        continue

                    # Parse published_at date
                    from datetime import datetime
                    published_at = None
                    if published_at_str:
                        try:
                            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                        except:
                            pass

                    # Save to database
                    saved_article = db.save_news_article(
                        symbol=stock.symbol,
                        title=title,
                        description=description,
                        url=url,
                        image_url=image_url,
                        source=source,
                        published_at=published_at
                    )

                    if saved_article:
                        saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving article for {stock.symbol}: {str(e)}")
                    continue

            result["articles_saved"] = saved_count
            result["articles_skipped"] = skipped_count
            result["success"] = True
            updated_count += 1
            total_articles_saved += saved_count

        except Exception as e:
            logger.error(f"Error updating news for {stock.symbol}: {str(e)}")
            result["error"] = str(e)
            failed_count += 1

        results.append(result)

    # Return summary
    return {
        "message": f"Updated news for {updated_count} of {len(active_stocks)} active stocks",
        "total_stocks": total_stocks,
        "active_stocks": len(active_stocks),
        "updated": updated_count,
        "failed": failed_count,
        "total_articles_saved": total_articles_saved,
        "results": results
    }
