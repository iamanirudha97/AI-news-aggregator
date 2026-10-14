import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.runner import run_all_scrapers
from app.services.process_anthropic import process_anthropic_markdown
from app.services.process_youtube import process_youtube_transcripts
from app.services.process_digest import process_digests
from app.services.process_email import send_digest_email

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

RECIPIENTS = [
    "sagarlm10@gmail.com",
    "sagarlm97@gmail.com",
]

def run_daily_pipeline(hours: int = 24, top_n: int = 10, recipients: list=None) -> dict:
    if recipients is None:
        recipients = RECIPIENTS

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("Starting Daily AI News Aggregator Pipeline")
    logger.info("=" * 60)
    
    results = {
        "start_time": start_time.isoformat(),
        "scraping": {},
        "processing": {},
        "digests": {},
        "email": {},
        "success": False
    }
    
    try:
        logger.info("\n[1/5] Scraping articles from sources...")
        scraping_results = run_all_scrapers(hours=hours)
        results["scraping"] = {
            "youtube": scraping_results.get("youtube", 0),
            "openai": scraping_results.get("openai", 0),
            "anthropic": scraping_results.get("anthropic", 0)
        }
        logger.info(f"✓ Scraped {results['scraping']['youtube']} YouTube videos, "
                    f"{results['scraping']['openai']} OpenAI articles, "
                    f"{results['scraping']['anthropic']} Anthropic articles")
        
        logger.info("\n[2/5] Processing Anthropic markdown...")
        anthropic_result = process_anthropic_markdown()
        results["processing"]["anthropic"] = anthropic_result
        logger.info(f"✓ Processed {anthropic_result['processed']} Anthropic articles "
                    f"({anthropic_result['failed']} failed)")
        
        logger.info("\n[3/5] Processing YouTube transcripts...")
        youtube_result = process_youtube_transcripts()
        results["processing"]["youtube"] = youtube_result
        logger.info(f"✓ Processed {youtube_result['processed']} transcripts "
                    f"({youtube_result['unavailable']} unavailable)")
        
        logger.info("\n[4/5] Creating digests for articles...")
        digest_result = process_digests()
        results["digests"] = digest_result
        logger.info(f"✓ Created {digest_result['processed']} digests "
                    f"({digest_result['failed']} failed out of {digest_result['total']} total)")
        
        logger.info("\n[5/5] Generating and sending email digest...")
        email_result = send_digest_email(hours=hours, top_n=top_n, recipients=RECIPIENTS)
        results["email"] = email_result
        
        if email_result["success"]:
            logger.info(f"✓ Email sent successfully with {email_result['articles_count']} articles")
            results["success"] = True
        else:
            logger.error(f"✗ Failed to send email: {email_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        results["error"] = str(e)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration
    
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline Summary")
    logger.info("=" * 60)
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Scraped: {results['scraping']}")
    logger.info(f"Processed: {results['processing']}")
    logger.info(f"Digests: {results['digests']}")
    logger.info(f"Email: {'Sent' if results['success'] else 'Failed'}")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    result = run_daily_pipeline(hours=24, top_n=10)
    exit(0 if result["success"] else 1)
